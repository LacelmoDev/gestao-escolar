from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from academico import views
from academico.views_relatorios import relatorio_turma, relatorios_admin
from academico.views_extras import pagina_404
from django.views.static import serve
import os
from academico.views_confirmacao import (
    confirmacao_matricula, confirmacao_estado, acesso_congelado,
    exportar_relatorio_excel, exportar_relatorio_pdf,
    exportar_relatorio_turma_excel, exportar_relatorio_turma_pdf,
)


handler404 = 'academico.views_extras.pagina_404'

# Bloqueia qualquer tentativa de acesso via /admin/
def bloquear_admin(request, *args, **kwargs):
    raise Http404

urlpatterns = [
    # Segurança: bloqueia /admin/ e /admin/login/ — retorna 404
    path('admin/', bloquear_admin),
    path('admin/login/', bloquear_admin),

    # Painel real — caminho obscuro
    path('tarimba-painel-2026/', admin.site.urls),

    path('', views.home, name='home'),
    path('precario/', views.precario, name='precario'),
    path('inscricao/<int:inscricao_id>/pdf/', views.gerar_pdf_inscricao, name='gerar_pdf_inscricao'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('verificar-perfil/', views.redirecionar_apos_login, name='verificar_perfil'),
    path('perfil/', views.perfil_aluno, name='perfil'),
    path('inscrever/', views.inscrever, name='inscrever'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('professor/dashboard/', views.dashboard_professor, name='professor_dashboard'),
    path('professor/turma/<int:turma_id>/', views.turma_detalhe, name='turma_detalhe'),
    path('professor/aluno/<int:aluno_id>/notas/', views.notas_aluno_json, name='notas_aluno_json'),
    path('professor/lancar-nota/', views.lancar_nota_rapida, name='lancar_nota_rapida'),
    path('professor/marcar-falta/', views.marcar_falta_rapida, name='marcar_falta_rapida'),
    path('professor/turma/<int:turma_id>/relatorio/', relatorio_turma, name='relatorio_turma'),
    path('justificar/', views.justificar_falta, name='justificar_falta'),
    path('professor/aprovar-falta/<int:presenca_id>/', views.aprovar_justificativa, name='aprovar_justificativa'),
    path('professor/rejeitar-falta/<int:presenca_id>/', views.rejeitar_justificativa, name='rejeitar_justificativa'),
    path('relatorios/', relatorios_admin, name='relatorios_admin'),
    path('favicon.ico', serve, {
        'path': 'images/favicon.ico',
        'document_root': os.path.join(settings.BASE_DIR, 'static'),
    }),
    path('confirmacao-matricula/', confirmacao_matricula, name='confirmacao_matricula'),
    path('confirmacao-estado/', confirmacao_estado, name='confirmacao_estado'),
    path('acesso-congelado/', acesso_congelado, name='acesso_congelado'),

    # Exportação Admin
    path('relatorios/exportar/excel/', exportar_relatorio_excel, name='exportar_relatorio_excel'),
    path('relatorios/exportar/pdf/', exportar_relatorio_pdf, name='exportar_relatorio_pdf'),

    # Exportação Professor
    path('professor/turma/<int:turma_id>/relatorio/excel/', exportar_relatorio_turma_excel, name='exportar_turma_excel'),
    path('professor/turma/<int:turma_id>/relatorio/pdf/', exportar_relatorio_turma_pdf, name='exportar_turma_pdf'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)