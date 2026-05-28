import random
import logging
from django.contrib import admin, messages
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from .models import Inscricao, Aluno, Nota, Presenca, RelatoriosDashboard
from usuarios.models import Usuario
from .utils import _enviar_notificacao_status, _enviar_email_boas_vindas


logger = logging.getLogger("academico")


def _gerar_senha():
    palavras = ["Tarimba", "Escola", "Aluno", "Gestao", "Portal"]
    palavra = random.choice(palavras)
    numeros = str(random.randint(10, 99))
    letras = get_random_string(4, "abcdefghjkmnpqrstuvwxyz")
    return f"{palavra}@{letras}{numeros}"


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'bi_numero', 'curso_pretendido', 'status', 'data_submissao')
    list_filter = ('status', 'curso_pretendido')
    actions = ['confirmar_para_pagamento', 'aprovar_e_gerar_aluno', 'rejeitar_inscricao']

    def save_model(self, request, obj, form, change):
        """Envia email de rejeição ao salvar manualmente com status REJEITADO."""
        if change and 'status' in form.changed_data and obj.status == 'REJEITADO':
            _enviar_notificacao_status(obj, 'REJEITADO')
            self.message_user(request, f"E-mail de rejeição enviado para {obj.nome_completo}.")
        super().save_model(request, obj, form, change)

    @admin.action(description="1. Confirmar Dados (Liberar para Pagamento)")
    def confirmar_para_pagamento(self, request, queryset):
        count = 0
        for inscricao in queryset.filter(status='PENDENTE'):
            inscricao.status = 'CONFIRMADO'
            inscricao.save(update_fields=['status'])
            _enviar_notificacao_status(inscricao, 'CONFIRMADO')
            count += 1

        if count:
            self.message_user(request, f"{count} inscrição(ões) confirmadas — candidato(s) notificado(s) por email.", messages.SUCCESS)
        else:
            self.message_user(request, "Nenhuma inscrição PENDENTE seleccionada.", messages.WARNING)

    @admin.action(description="2. Validar Pagamento e Criar Aluno Oficial")
    def aprovar_e_gerar_aluno(self, request, queryset):
        from escola.models import Turma
        criados, ignorados = 0, 0

        for inscricao in queryset.filter(status='CONFIRMADO'):
            if Usuario.objects.filter(username=inscricao.bi_numero).exists():
                self.message_user(request, f"⚠️ Utilizador {inscricao.bi_numero} já existe — ignorado.", messages.WARNING)
                ignorados += 1
                continue

            senha_temp = _gerar_senha()

            novo_usuario = Usuario.objects.create_user(
                username=inscricao.bi_numero,
                password=senha_temp,
                first_name=inscricao.nome_completo.split()[0],
                last_name=' '.join(inscricao.nome_completo.split()[1:]),
                email=inscricao.email or "",
            )
            novo_usuario.is_aluno = True
            novo_usuario.save()

            turma_alocada = Turma.objects.filter(
                classe=str(inscricao.classe_pretendida),
                curso=inscricao.curso_pretendido,
            ).first()

            num_proc = f"2026/{inscricao.id:03d}"
            Aluno.objects.create(
                usuario=novo_usuario,
                numero_processo=num_proc,
                turma=turma_alocada,
            )

            inscricao.status = 'PAGO'
            inscricao.save(update_fields=['status'])

            # Email de boas-vindas com credenciais
            _enviar_email_boas_vindas(inscricao, novo_usuario, senha_temp, turma_alocada, num_proc)
            criados += 1

        if criados:
            self.message_user(request, f"✅ {criados} aluno(s) criado(s) — credenciais enviadas por email.", messages.SUCCESS)
        if not criados and not ignorados:
            self.message_user(request, "Nenhuma inscrição com status 'Dados Confirmados' seleccionada. Execute primeiro a acção 1.", messages.WARNING)

    @admin.action(description="3. Rejeitar Inscrição")
    def rejeitar_inscricao(self, request, queryset):
        count = 0
        for inscricao in queryset.exclude(status='PAGO'):
            inscricao.status = 'REJEITADO'
            inscricao.save(update_fields=['status'])
            _enviar_notificacao_status(inscricao, 'REJEITADO')
            count += 1

        if count:
            self.message_user(request, f"{count} inscrição(ões) rejeitada(s) — candidato(s) notificado(s).", messages.SUCCESS)
        else:
            self.message_user(request, "Nenhuma inscrição elegível para rejeição.", messages.WARNING)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('numero_processo', 'get_nome', 'turma')

    def get_nome(self, obj):
        return obj.usuario.get_full_name()
    get_nome.short_description = 'Nome'


admin.site.register(Nota)
admin.site.register(Presenca)


@admin.register(RelatoriosDashboard)
class RelatoriosDashboardAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('/relatorios/')

    def has_add_permission(self, request):
        return False
