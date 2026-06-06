import random
import logging
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from .models import Inscricao, Aluno, ConfirmacaoMatricula, Nota, Presenca, RelatoriosDashboard, Notificacao
from .services import get_ano_letivo_atual
from usuarios.models import Usuario
from .utils import _enviar_notificacao_status, _enviar_email_boas_vindas

logger = logging.getLogger("academico")


# ── Sobrepõe o AdminSite para injectar notificações no index ───────────────
# Fazemos isto aqui em vez de urls.py para evitar monkey-patching frágil

_original_index = admin.AdminSite.index

def _index_com_notificacoes(self, request, extra_context=None):
    extra_context = extra_context or {}
    try:
        extra_context['inscricoes_pendentes'] = (
            Inscricao.objects
            .filter(status='PENDENTE')
            .select_related('curso_pretendido')
            .order_by('-data_submissao')[:10]
        )
        from .models import ConfirmacaoMatricula
        extra_context['confirmacoes_pendentes'] = (
            ConfirmacaoMatricula.objects
            .filter(status='EM_REVISAO')
            .select_related('aluno__usuario', 'curso_novo')
            .order_by('-data_submissao')[:10]
        )
    except Exception:
        extra_context['inscricoes_pendentes'] = []
    return _original_index(self, request, extra_context=extra_context)

admin.AdminSite.index = _index_com_notificacoes
admin.site.site_header = "Colégio Tarimba — Administração"
admin.site.site_title = "Tarimba Admin"
admin.site.index_title = "Painel de Controlo"


# ── Helpers ────────────────────────────────────────────────────────────────

def _gerar_senha():
    palavras = ["Tarimba", "Escola", "Aluno", "Gestao", "Portal"]
    palavra = random.choice(palavras)
    numeros = str(random.randint(10, 99))
    letras = get_random_string(4, "abcdefghjkmnpqrstuvwxyz")
    return f"{palavra}@{letras}{numeros}"


# ── InscricaoAdmin ─────────────────────────────────────────────────────────

@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'bi_numero', 'curso_pretendido', 'status', 'data_submissao')
    list_filter = ('status', 'curso_pretendido')
    actions = ['confirmar_para_pagamento', 'aprovar_e_gerar_aluno', 'rejeitar_inscricao']

    def save_model(self, request, obj, form, change):
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

            ano_atual = get_ano_letivo_atual()
            num_proc = f"{ano_atual}/{inscricao.id:03d}"
            Aluno.objects.create(
                usuario=novo_usuario,
                numero_processo=num_proc,
                turma=turma_alocada,
            )

            inscricao.status = 'PAGO'
            inscricao.save(update_fields=['status'])
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


# ── AlunoAdmin ─────────────────────────────────────────────────────────────

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('numero_processo', 'get_nome', 'turma', 'esta_congelado')
    list_filter = ('turma', 'esta_congelado')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'numero_processo')
    actions = ['congelar_alunos', 'descongelar_alunos']

    def get_nome(self, obj):
        return obj.usuario.get_full_name()
    get_nome.short_description = 'Nome'

    @admin.action(description='Congelar alunos selecionados')
    def congelar_alunos(self, request, queryset):
        updated = queryset.update(esta_congelado=True)
        self.message_user(request, f'{updated} aluno(s) congelado(s) com sucesso.', messages.SUCCESS)

    @admin.action(description='Descongelar alunos selecionados')
    def descongelar_alunos(self, request, queryset):
        updated = queryset.update(esta_congelado=False)
        self.message_user(request, f'{updated} aluno(s) descongelado(s) com sucesso.', messages.SUCCESS)


@admin.register(ConfirmacaoMatricula)
class ConfirmacaoMatriculaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_aluno_nome', 'nome_completo', 'bi_numero', 'email',
        'classe_nova', 'curso_novo', 'status', 'ano_letivo', 'data_submissao'
    )
    list_filter = ('status', 'ano_letivo')
    search_fields = ('nome_completo', 'bi_numero', 'email', 'aluno__numero_processo')
    readonly_fields = ('data_submissao', 'data_atualizacao')
    actions = ['aprovar_confirmacao', 'marcar_aguardando_pagamento', 'rejeitar_confirmacao']

    def get_aluno_nome(self, obj):
        if obj.aluno:
            return obj.aluno.usuario.get_full_name() or obj.aluno.usuario.username
        return obj.nome_completo or 'Visitante'
    get_aluno_nome.short_description = 'Aluno / Visitante'

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'ATIVO' and obj.aluno:
                obj.aluno.esta_congelado = False
                obj.aluno.save(update_fields=['esta_congelado'])
            from academico.views_confirmacao import _email_confirmacao
            _email_confirmacao(obj, obj.status)
        super().save_model(request, obj, form, change)

    @admin.action(description='Aprovar Confirmação de Matrícula')
    def aprovar_confirmacao(self, request, queryset):
        count = 0
        from academico.views_confirmacao import _email_confirmacao
        from escola.models import Turma
        for confirmacao in queryset.exclude(status='ATIVO'):
            turma_alocada = None
            try:
                turma_filtro = {
                    'classe': str(confirmacao.classe_nova),
                    'ano_letivo': confirmacao.ano_letivo,
                }
                if confirmacao.curso_novo:
                    turma_filtro['curso'] = confirmacao.curso_novo
                elif confirmacao.aluno and confirmacao.aluno.turma:
                    turma_filtro['curso'] = confirmacao.aluno.turma.curso

                turma_alocada = Turma.objects.filter(**turma_filtro).first()
                if not turma_alocada:
                    # fallback: procura a turma seguinte disponível com mesma classe/curso
                    base_filtro = {'classe': str(confirmacao.classe_nova)}
                    if confirmacao.curso_novo:
                        base_filtro['curso'] = confirmacao.curso_novo
                    elif confirmacao.aluno and confirmacao.aluno.turma:
                        base_filtro['curso'] = confirmacao.aluno.turma.curso
                    if base_filtro.get('curso'):
                        turma_alocada = Turma.objects.filter(
                            **base_filtro,
                            ano_letivo__gte=confirmacao.ano_letivo
                        ).order_by('ano_letivo').first()
            except Exception:
                turma_alocada = None

            if confirmacao.aluno:
                if turma_alocada:
                    confirmacao.aluno.turma = turma_alocada
                confirmacao.aluno.esta_congelado = False
                confirmacao.aluno.save(update_fields=['turma', 'esta_congelado'])

            confirmacao.status = 'ATIVO'
            confirmacao.save(update_fields=['status'])
            _email_confirmacao(confirmacao, 'ATIVO')
            count += 1
        self.message_user(request, f'{count} confirmação(ões) aprovadas e e-mail enviado(s).', messages.SUCCESS)

    @admin.action(description='Marcar como Aguardando Pagamento')
    def marcar_aguardando_pagamento(self, request, queryset):
        count = 0
        from academico.views_confirmacao import _email_confirmacao
        for confirmacao in queryset.exclude(status='AGUARDANDO_PAGAMENTO'):
            confirmacao.status = 'AGUARDANDO_PAGAMENTO'
            confirmacao.save(update_fields=['status'])
            _email_confirmacao(confirmacao, 'AGUARDANDO_PAGAMENTO')
            count += 1
        self.message_user(request, f'{count} confirmação(ões) atualizada(s) para aguardando pagamento.', messages.SUCCESS)

    @admin.action(description='Rejeitar Confirmação de Matrícula')
    def rejeitar_confirmacao(self, request, queryset):
        count = 0
        from academico.views_confirmacao import _email_confirmacao
        for confirmacao in queryset.exclude(status='REJEITADO'):
            confirmacao.status = 'REJEITADO'
            confirmacao.save(update_fields=['status'])
            _email_confirmacao(confirmacao, 'REJEITADO')
            count += 1
        self.message_user(request, f'{count} confirmação(ões) rejeitada(s) e e-mail enviado(s).', messages.SUCCESS)


admin.site.register(Nota)
admin.site.register(Presenca)


# ── RelatoriosDashboard — link para relatórios ─────────────────────────────

@admin.register(RelatoriosDashboard)
class RelatoriosDashboardAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('/relatorios/')

    def has_add_permission(self, request):
        return False


# ── Notificacao — NÃO registada no admin (não deve aparecer no menu) ───────
# O modelo existe apenas para uso interno — as notificações são mostradas
# directamente no index do admin via o contexto injectado acima.
# Se precisares gerir notificações manualmente, descomenta as linhas abaixo:
#
# @admin.register(Notificacao)
# class NotificacaoAdmin(admin.ModelAdmin):
#     list_display = ('inscricao_nome', 'tipo', 'lida', 'data_criacao')
#     readonly_fields = ('data_criacao', 'data_leitura')
#
#     def inscricao_nome(self, obj):
#         return obj.inscricao.nome_completo
#     inscricao_nome.short_description = 'Inscrição'
#
#     def has_add_permission(self, request):
#         return False
