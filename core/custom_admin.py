from django.contrib.admin import AdminSite
from academico.models import Inscricao, Notificacao


class TarimbaAdminSite(AdminSite):
    site_header = "Colégio Tarimba — Administração"
    site_title = "Tarimba Admin"
    index_title = "Painel de Controlo"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['inscricoes_pendentes'] = Inscricao.objects.filter(
            status='PENDENTE'
        ).select_related('curso_pretendido').order_by('-data_submissao')[:10]
        
        # Adicionar notificações não lidas
        extra_context['notificacoes_nao_lidas'] = Notificacao.objects.filter(
            lida=False
        ).select_related('inscricao').order_by('-data_criacao')[:10]
        
        return super().index(request, extra_context=extra_context)


tarimba_admin = TarimbaAdminSite(name='tarimba_admin')
