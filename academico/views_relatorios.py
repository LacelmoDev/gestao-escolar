from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Avg, Q
from decimal import Decimal
import json
from .models import Nota, Aluno, Presenca, Inscricao, AnoLetivo
from .services import get_ano_letivo_atual
from escola.models import Turma, Disciplina, Curso, Professor, Atribuicao

@login_required
def relatorios_admin(request):
    """
    Painel de relatórios para o administrador.
    Aceita utilizadores com is_staff=True OU is_admin_escola=True.
    """
    if not (request.user.is_staff or request.user.is_admin_escola):
        raise PermissionDenied

    ano = int(request.GET.get('ano', get_ano_letivo_atual()))

    # ── 1. INSCRIÇÕES POR STATUS ──────────────────────────────────────────
    inscricoes_status = Inscricao.objects.values('status').annotate(
        total=Count('id')
    ).order_by('status')
    anos_disponiveis = [2026]
    status_labels = []
    status_dados = []
    status_map = {
        'PENDENTE': 'Pendente',
        'CONFIRMADO': 'Confirmado',
        'PAGO': 'Pago',
        'REJEITADO': 'Rejeitado',
    }
    for item in inscricoes_status:
        status_labels.append(status_map.get(item['status'], item['status']))
        status_dados.append(item['total'])

    total_inscricoes = sum(status_dados)
    anos_disponiveis = list(AnoLetivo.objects.order_by('-ano').values_list('ano', flat=True))
    if not anos_disponiveis:
        anos_disponiveis = [get_ano_letivo_atual()]

    # ── 2. ALUNOS POR TURMA ───────────────────────────────────────────────
    turmas_dados = Turma.objects.filter(
        ano_letivo=ano
    ).annotate(
        num_alunos=Count('alunos')
    ).order_by('curso__nome', 'classe')

    turmas_labels = [str(t) for t in turmas_dados]
    turmas_alunos = [t.num_alunos for t in turmas_dados]
    total_alunos = sum(turmas_alunos)

    # ── 3. MÉDIAS POR DISCIPLINA ─────────────────
    notas_qs = Nota.objects.filter(
        aluno__turma__ano_letivo=ano
    ).select_related('disciplina')

    medias_por_disciplina = {}
    for nota in notas_qs:
        nome = nota.disciplina.nome
        media = float(nota.media_trimestral)
        if nome not in medias_por_disciplina:
            medias_por_disciplina[nome] = []
        medias_por_disciplina[nome].append(media)

    disciplinas_labels = []
    disciplinas_medias = []
    for disc, vals in sorted(medias_por_disciplina.items()):
        disciplinas_labels.append(disc)
        media_final = round(sum(vals) / len(vals), 1) if vals else 0
        disciplinas_medias.append(media_final)

    # ── 4. ASSIDUIDADE POR TURMA ──────────────────────────────────────────
    assiduidade_labels = []
    assiduidade_presentes = []
    assiduidade_faltas = []

    for turma in turmas_dados:
        alunos_turma = Aluno.objects.filter(turma=turma)
        total_registos = Presenca.objects.filter(aluno__in=alunos_turma).count()
        total_faltas = Presenca.objects.filter(
            aluno__in=alunos_turma, esta_presente=False
        ).count()
        total_presentes = total_registos - total_faltas

        if total_registos > 0:
            assiduidade_labels.append(turma.nome)
            assiduidade_presentes.append(total_presentes)
            assiduidade_faltas.append(total_faltas)

    # ── 5. INDICADORES GERAIS ─────────────────────────────────────────────
    total_professores = Professor.objects.count()
    total_turmas = turmas_dados.count()
    total_faltas_global = Presenca.objects.filter(
        esta_presente=False,
        aluno__turma__ano_letivo=ano
    ).count()
    total_faltas_justificadas = Presenca.objects.filter(
        esta_presente=False,
        justificada=True,
        aluno__turma__ano_letivo=ano
    ).count()
    pct_justificadas = round(
        (total_faltas_justificadas / total_faltas_global * 100)
        if total_faltas_global > 0 else 0, 1
    )

    context = {
        'ano': ano,
        'status_labels': json.dumps(status_labels),
        'status_dados': json.dumps(status_dados),
        'total_inscricoes': total_inscricoes,
        'turmas_labels': json.dumps(turmas_labels),
        'turmas_alunos': json.dumps(turmas_alunos),
        'total_alunos': total_alunos,
        'anos_disponiveis': anos_disponiveis,
        'disciplinas_labels': json.dumps(disciplinas_labels),
        'disciplinas_medias': json.dumps(disciplinas_medias),
        'assiduidade_labels': json.dumps(assiduidade_labels),
        'assiduidade_presentes': json.dumps(assiduidade_presentes),
        'assiduidade_faltas': json.dumps(assiduidade_faltas),
        'total_professores': total_professores,
        'total_turmas': total_turmas,
        'total_faltas_global': total_faltas_global,
        'pct_justificadas': pct_justificadas,
        'ano': ano,
        'anos_disponiveis': anos_disponiveis,
    }

    return render(request, 'academico/relatorios_admin.html', context)

@login_required
def relatorio_turma(request, turma_id):
    """
    Relatório detalhado de uma turma para o professor.
    Mostra:
    - Médias por aluno e disciplina
    - Ranking de desempenho
    - Assiduidade individual
    - Distribuição de notas (aprovados/reprovados)
    """
    if not request.user.is_professor:
        raise PermissionDenied

    professor = Professor.objects.get(usuario=request.user)
    turma = Turma.objects.get(id=turma_id)
    if not Atribuicao.objects.filter(professor=professor, turma=turma).exists():
        raise PermissionDenied

    alunos = Aluno.objects.filter(turma=turma).select_related('usuario').order_by(
        'usuario__first_name'
    )

    disciplinas = Disciplina.objects.filter(
        atribuicao__professor=professor,
        atribuicao__turma=turma
    )

    # ── Médias por aluno ──────────────────────────────────────────────────
    dados_alunos = []
    for aluno in alunos:
        notas_aluno = Nota.objects.filter(
            aluno=aluno, disciplina__in=disciplinas
        )
        medias = [float(n.media_trimestral) for n in notas_aluno]
        media_geral = round(sum(medias) / len(medias), 1) if medias else 0

        total_faltas = Presenca.objects.filter(
            aluno=aluno,
            disciplina__in=disciplinas,
            esta_presente=False
        ).count()

        dados_alunos.append({
            'nome': aluno.usuario.get_full_name() or aluno.usuario.username,
            'media': media_geral,
            'faltas': total_faltas,
            'aprovado': media_geral >= 10,
        })

    dados_alunos.sort(key=lambda x: x['media'], reverse=True)

    # ── Dados para os gráficos ────────────────────────────────────────────
    nomes = [d['nome'].split()[0] for d in dados_alunos]  # primeiro nome
    medias_lista = [d['media'] for d in dados_alunos]
    faltas_lista = [d['faltas'] for d in dados_alunos]

    aprovados = sum(1 for d in dados_alunos if d['aprovado'])
    reprovados = len(dados_alunos) - aprovados

    # ── Médias por disciplina (nesta turma) ───────────────────────────────
    medias_disc_labels = []
    medias_disc_dados = []
    for disc in disciplinas:
        notas_disc = Nota.objects.filter(aluno__in=alunos, disciplina=disc)
        vals = [float(n.media_trimestral) for n in notas_disc]
        media_disc = round(sum(vals) / len(vals), 1) if vals else 0
        medias_disc_labels.append(disc.nome)
        medias_disc_dados.append(media_disc)

    context = {
        'turma': turma,
        'professor': professor,
        'dados_alunos': dados_alunos,
        'total_alunos': len(dados_alunos),
        'aprovados': aprovados,
        'reprovados': reprovados,
        # Gráficos
        'nomes_json': json.dumps(nomes),
        'medias_json': json.dumps(medias_lista),
        'faltas_json': json.dumps(faltas_lista),
        'medias_disc_labels': json.dumps(medias_disc_labels),
        'medias_disc_dados': json.dumps(medias_disc_dados),
    }

    return render(request, 'academico/relatorio_turma.html', context)
