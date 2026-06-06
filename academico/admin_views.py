from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
import json

from .models import Nota, Aluno, Presenca, Inscricao, AnoLetivo
from .services import get_ano_letivo_atual
from escola.models import Turma, Professor

@staff_member_required
def relatorios_admin_view(request):
    ano = int(request.GET.get('ano', get_ano_letivo_atual()))

    inscricoes_status = Inscricao.objects.values('status').annotate(total=Count('id')).order_by('status')
    status_map = {'PENDENTE': 'Pendente', 'CONFIRMADO': 'Confirmado', 'PAGO': 'Pago', 'REJEITADO': 'Rejeitado'}
    status_labels = [status_map.get(i['status'], i['status']) for i in inscricoes_status]
    status_dados  = [i['total'] for i in inscricoes_status]
    total_inscricoes = sum(status_dados)
    anos_disponiveis = list(AnoLetivo.objects.order_by('-ano').values_list('ano', flat=True))
    if not anos_disponiveis:
        anos_disponiveis = [get_ano_letivo_atual()]

    turmas_dados  = Turma.objects.filter(ano_letivo=ano).annotate(num_alunos=Count('alunos')).order_by('curso__nome', 'classe')
    turmas_labels = [str(t) for t in turmas_dados]
    turmas_alunos = [t.num_alunos for t in turmas_dados]
    total_alunos  = sum(turmas_alunos)

    notas_qs = Nota.objects.filter(aluno__turma__ano_letivo=ano).select_related('disciplina')
    medias_por_disciplina = {}
    for nota in notas_qs:
        nome = nota.disciplina.nome
        medias_por_disciplina.setdefault(nome, []).append(float(nota.media_trimestral))
    disciplinas_labels = sorted(medias_por_disciplina.keys())
    disciplinas_medias = [
        round(sum(medias_por_disciplina[d]) / len(medias_por_disciplina[d]), 1)
        for d in disciplinas_labels
    ]

    assiduidade_labels, assiduidade_presentes, assiduidade_faltas = [], [], []
    for turma in turmas_dados:
        alunos_turma = Aluno.objects.filter(turma=turma)
        total_reg    = Presenca.objects.filter(aluno__in=alunos_turma).count()
        total_flt    = Presenca.objects.filter(aluno__in=alunos_turma, esta_presente=False).count()
        if total_reg > 0:
            assiduidade_labels.append(turma.nome)
            assiduidade_presentes.append(total_reg - total_flt)
            assiduidade_faltas.append(total_flt)

    total_professores   = Professor.objects.count()
    total_turmas        = turmas_dados.count()
    total_faltas_global = Presenca.objects.filter(esta_presente=False, aluno__turma__ano_letivo=ano).count()
    total_justificadas  = Presenca.objects.filter(esta_presente=False, justificada=True, aluno__turma__ano_letivo=ano).count()
    pct_justificadas    = round((total_justificadas / total_faltas_global * 100) if total_faltas_global > 0 else 0, 1)

    context = {
        'title': 'Relatórios e Estatísticas',
        'has_permission': True,
        'ano': ano,
        'status_labels':         json.dumps(status_labels),
        'status_dados':          json.dumps(status_dados),
        'total_inscricoes':      total_inscricoes,
        'turmas_labels':         json.dumps(turmas_labels),
        'turmas_alunos':         json.dumps(turmas_alunos),
        'total_alunos':          total_alunos,
        'disciplinas_labels':    json.dumps(disciplinas_labels),
        'disciplinas_medias':    json.dumps(disciplinas_medias),
        'assiduidade_labels':    json.dumps(assiduidade_labels),
        'assiduidade_presentes': json.dumps(assiduidade_presentes),
        'assiduidade_faltas':    json.dumps(assiduidade_faltas),
        'total_professores':     total_professores,
        'total_turmas':          total_turmas,
        'total_faltas_global':   total_faltas_global,
        'pct_justificadas':      pct_justificadas,
    }
    return render(request, 'admin/relatorios.html', context)