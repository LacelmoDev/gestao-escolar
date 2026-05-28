from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from escola.models import Curso, Turma, Disciplina, Professor, Atribuicao, GradeCurricular
from academico.models import Aluno


class Command(BaseCommand):
    help = 'Povoa o banco de dados com dados iniciais do sistema Tarimba'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        self.stdout.write("🚀 Iniciando o Povoamento Mestre (Versão Integrada)...")

        # --- 1. CURSOS ---
        cursos_info = {
            'PRIMARIO':   Curso.objects.get_or_create(nome="Ensino Primário",                    tipo='PRIMARIO')[0],
            'I_CICLO':    Curso.objects.get_or_create(nome="I Ciclo do Ensino Secundário",        tipo='I_CICLO')[0],
            'CEJ':        Curso.objects.get_or_create(nome="Ciências Económicas-Jurídicas",       tipo='GERAL')[0],
            'CFB':        Curso.objects.get_or_create(nome="Ciências Físicas e Biológicas",       tipo='GERAL')[0],
            'INF_GEST':   Curso.objects.get_or_create(nome="Informática de Gestão",               tipo='TECNICO')[0],
            'CONT_GERAL': Curso.objects.get_or_create(nome="Contabilidade Geral",                 tipo='TECNICO')[0],
        }

        # --- 2. TURMAS (baseado no PDF de estrutura) ---
        self.stdout.write("🏫 Criando Turmas...")

        turmas_config = [
            # Ensino Primário — Manhã
            {'curso': 'PRIMARIO', 'classe': 'INI', 'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '1',   'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '1',   'nome': 'B',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '2',   'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '2',   'nome': 'B',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '3',   'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '3',   'nome': 'B',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '4',   'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '4',   'nome': 'B',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '5',   'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '5',   'nome': 'B',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '6',   'nome': 'A',   'turno': 'MANHA'},
            {'curso': 'PRIMARIO', 'classe': '6',   'nome': 'B',   'turno': 'MANHA'},

            # I Ciclo — Manhã
            {'curso': 'I_CICLO', 'classe': '7', 'nome': 'A',  'turno': 'MANHA'},
            {'curso': 'I_CICLO', 'classe': '7', 'nome': 'B',  'turno': 'MANHA'},
            {'curso': 'I_CICLO', 'classe': '8', 'nome': 'A',  'turno': 'MANHA'},
            {'curso': 'I_CICLO', 'classe': '8', 'nome': 'B',  'turno': 'MANHA'},
            {'curso': 'I_CICLO', 'classe': '9', 'nome': 'A',  'turno': 'MANHA'},
            {'curso': 'I_CICLO', 'classe': '9', 'nome': 'B',  'turno': 'MANHA'},

            # I Ciclo — Tarde
            {'curso': 'I_CICLO', 'classe': '7', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'I_CICLO', 'classe': '8', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'I_CICLO', 'classe': '8', 'nome': 'T2', 'turno': 'TARDE'},
            {'curso': 'I_CICLO', 'classe': '9', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'I_CICLO', 'classe': '9', 'nome': 'T2', 'turno': 'TARDE'},

            # Informática de Gestão — Tarde
            {'curso': 'INF_GEST', 'classe': '10', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'INF_GEST', 'classe': '10', 'nome': 'T2', 'turno': 'TARDE'},
            {'curso': 'INF_GEST', 'classe': '11', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'INF_GEST', 'classe': '12', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'INF_GEST', 'classe': '13', 'nome': 'T1', 'turno': 'TARDE'},

            # Contabilidade Geral — Tarde
            {'curso': 'CONT_GERAL', 'classe': '10', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CONT_GERAL', 'classe': '11', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CONT_GERAL', 'classe': '12', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CONT_GERAL', 'classe': '13', 'nome': 'T1', 'turno': 'TARDE'},

            # Ciências Físicas e Biológicas — Tarde
            {'curso': 'CFB', 'classe': '10', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CFB', 'classe': '11', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CFB', 'classe': '12', 'nome': 'T1', 'turno': 'TARDE'},

            # Ciências Económicas-Jurídicas — Tarde
            {'curso': 'CEJ', 'classe': '10', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CEJ', 'classe': '11', 'nome': 'T1', 'turno': 'TARDE'},
            {'curso': 'CEJ', 'classe': '12', 'nome': 'T1', 'turno': 'TARDE'},
        ]

        self.stdout.write("🏫 Criando Turmas...")
        criadas = 0
        erros = 0
        for t in turmas_config:
            try:
                obj, created = Turma.objects.get_or_create(
                curso=cursos_info[t['curso']],
                classe=t['classe'],
                nome=t['nome'],
                defaults={'turno': t['turno']}
                )
                if created:
                    criadas += 1
                    self.stdout.write(f"  ✔ Criada: {obj}")
                else:
                    self.stdout.write(f"  ℹ️  Já existe: {obj}")
            except Exception as e:
                erros += 1
                self.stdout.write(self.style.ERROR(
                f"  ❌ Erro ao criar turma {t}: {e}"
                ))

        self.stdout.write(f"  Resultado: {criadas} criadas, {erros} erros.")
        # --- 3. GRADE CURRICULAR ---
        grade_completa = {
            'INI': {'PRIMARIO': ["Comunicação Linguística", "Meio Físico e Social", "Expressão Matemática", "Representação Manual e Plástica", "Educação Musical"]},
            '1':   {'PRIMARIO': ["Língua Portuguesa", "Estudo do Meio", "Matemática", "Educação Manual e Plástica", "Educação Musical"]},
            '2':   {'PRIMARIO': ["Língua Portuguesa", "Estudo do Meio", "Matemática", "Educação Manual e Plástica", "Educação Musical"]},
            '3':   {'PRIMARIO': ["Língua Portuguesa", "Estudo do Meio", "Matemática", "Educação Manual e Plástica", "Educação Musical"]},
            '4':   {'PRIMARIO': ["Língua Portuguesa", "Estudo do Meio", "Caligrafia", "Matemática", "Educação Manual e Plástica", "Língua Estrangeira (Inglês)", "Educação Musical", "Língua Nacional"]},
            '5':   {'PRIMARIO': ["Língua Portuguesa", "Ciências da Natureza", "Caligrafia", "Matemática", "Inglês", "Educação Manual e Plástica", "Geografia", "História", "Educação Moral e Cívica", "Informática", "Educação Musical", "Língua Nacional"]},
            '6':   {'PRIMARIO': ["Língua Portuguesa", "Ciências da Natureza", "Caligrafia", "Matemática", "Inglês", "Educação Manual e Plástica", "Geografia", "História", "Educação Moral e Cívica", "Informática", "Educação Musical", "Língua Nacional"]},
            '7':   {'I_CICLO': ["Língua Portuguesa", "Biologia", "Matemática", "Física", "História", "Química", "Educação Laboral", "Caligrafia", "Geografia", "Inglês", "Educação Visual e Plástica (E.V.P.)", "Educação Moral e Cívica (E.M.C.)", "Empreendedorismo", "Educacao fisica"]},
            '8':   {'I_CICLO': ["Língua Portuguesa", "Biologia", "Matemática", "Física", "História", "Química", "Educação Laboral", "Caligrafia", "Geografia", "Inglês", "Educação Visual e Plástica (E.V.P.)", "Educação Moral e Cívica (E.M.C.)", "Empreendedorismo", "Educacao fisica"]},
            '9':   {'I_CICLO': ["Língua Portuguesa", "Biologia", "Matemática", "Física", "História", "Química", "Educação Laboral", "Caligrafia", "Geografia", "Inglês", "Educação Visual e Plástica (E.V.P.)", "Educação Moral e Cívica (E.M.C.)", "Empreendedorismo", "Educacao fisica"]},
            '10': {
                'CEJ':        ["Língua Portuguesa", "Inglês", "Filosofia", "Matemática", "História", "Geografia", "Informática", "Introdução ao Direito", "Empreendedorismo", "Introdução à Economia"],
                'CFB':        ["Língua Portuguesa", "Inglês", "Matemática", "Química", "Biologia", "Física", "Informática", "Empreendedorismo"],
                'INF_GEST':   ["Língua Portuguesa", "Inglês", "Matemática", "TIC", "FAI", "TLP", "OAE", "BD"],
                'CONT_GERAL': ["Língua Portuguesa", "Inglês", "Matemática", "Contabilidade Financeira", "Formação de Atitudes Integradoras", "Economia", "Introdução à Auditoria e Controlo (IAC)", "Direito Laboral e Comercial (DLC)", "Administração de Empresas"],
            },
            '11': {
                'CEJ':        ["Língua Portuguesa", "Inglês", "Filosofia", "Matemática", "História", "Geografia", "Informática", "Introdução ao Direito", "Empreendedorismo", "Introdução à Economia"],
                'CFB':        ["Língua Portuguesa", "Inglês", "Filosofia", "Matemática", "Química", "Psicologia", "Biologia", "Geologia", "Física", "Empreendedorismo"],
                'INF_GEST':   ["Língua Portuguesa", "Inglês", "Matemática", "Informatica Aplicada a gestao", "Formação de Atitudes Integradoras", "TLP", "Organizacao Administracao de Empresas", "Redes de Computadores (RC)"],
                'CONT_GERAL': ["Língua Portuguesa", "Inglês", "Matemática", "Contabilidade Financeira", "Formação de Atitudes Integradoras", "Introdução à Auditoria e Controlo (IAC)", "Direito", "Administração de Empresas"],
            },
            '12': {
                'CEJ':        ["Língua Portuguesa", "História", "Filosofia", "Psicologia", "Inglês", "Geografia", "MIC", "D.E.S", "Empreendedorismo", "Introdução ao Direito", "Introducao a economia"],
                'CFB':        ["Língua Portuguesa", "Biologia", "Filosofia", "Matemática", "Psicologia", "Inglês", "MIC", "Empreendedorismo", "Química", "Física"],
                'INF_GEST':   ["Sistemas de Informação (SI)", "TIC", "Matemática", "IMEI", "Informatica Aplicada a gestao", "TLP", "Projeto Tecnológico (PT)", "Organizacao Administracao de Empresas", "Empreendedorismo"],
                'CONT_GERAL': ["Sociologia", "Contabilidade Analítica", "Matemática", "Análise Económica e Financeira (AEF)", "Técnica de Comunicação Empresarial (TCE)", "Projeto Tecnológico (PT)", "Direito Laboral e Comercial (DLC)"],
            },
            '13': {
                'INF_GEST':   ["Projeto Tecnológico (PT)"],
                'CONT_GERAL': ["Projeto Tecnológico (PT)"],
            },
        }

        self.stdout.write("📚 Criando Disciplinas e Grades Curriculares...")
        for classe, cursos_dict in grade_completa.items():
            for curso_key, disciplinas in cursos_dict.items():
                curso_obj = cursos_info[curso_key]
                for d_nome in disciplinas:
                    disc_obj, _ = Disciplina.objects.get_or_create(nome=d_nome)
                    GradeCurricular.objects.get_or_create(curso=curso_obj, disciplina=disc_obj, classe=classe)

        # --- 4. PROFESSORES E ATRIBUIÇÕES ---
        self.stdout.write("👨‍🏫 Vinculando Professores...")
        profs_config = [
            {'nome': 'Robson Santos',   'user': 'robson',   'espec': 'TI',     'matérias': ["TLP", "IMEI"]},
            {'nome': 'Mateus Jose',     'user': 'mateus',   'espec': 'PT',     'matérias': ["Projeto Tecnológico"]},
            {'nome': 'Domingos Kipipa', 'user': 'domingos', 'espec': 'Redes',  'matérias': ["Banco de Dados", "Redes de Computadores", "TIC"]},
            {'nome': 'Fedao Cunha',     'user': 'fedao',    'espec': 'Exatas', 'matérias': ["Matemática", "Física", "Química"]},
            {'nome': 'Fernanda Manuel', 'user': 'fernanda', 'espec': 'Línguas','matérias': ["Língua Portuguesa"]},
        ]

        for p in profs_config:
            u, _ = User.objects.get_or_create(
                username=p['user'],
                defaults={'first_name': p['nome'].split()[0], 'is_professor': True}
            )
            u.set_password('tarimba123')
            u.save()

            prof, _ = Professor.objects.get_or_create(
                usuario=u,
                defaults={'especialidade': p['espec']}
            )

            for t in Turma.objects.all():
                for d_nome in p['matérias']:
                    disc = Disciplina.objects.filter(nome__icontains=d_nome).first()
                    if disc and GradeCurricular.objects.filter(curso=t.curso, classe=t.classe, disciplina=disc).exists():
                        Atribuicao.objects.get_or_create(professor=prof, disciplina=disc, turma=t)

        # --- 5. ALUNOS ---
        self.stdout.write("🎓 Matriculando Alunos...")
        alunos_docs = [
            {'nome': 'Erikson Pereira',  'user': 'erikson',   'classe': '10', 'curso': 'INF_GEST',  'turma': 'T1'},
            {'nome': 'Finoel Francisco', 'user': 'finoel',    'classe': '7',  'curso': 'I_CICLO',   'turma': 'T1'},
            {'nome': 'Mariineza Viegas', 'user': 'mariineza', 'classe': '12', 'curso': 'INF_GEST',  'turma': 'T1'},
            {'nome': 'Conceicao Lima',   'user': 'conceicao', 'classe': '11', 'curso': 'INF_GEST',  'turma': 'T1'},
            {'nome': 'Octavio Simoes',   'user': 'octavio',   'classe': '13', 'curso': 'INF_GEST',  'turma': 'T1'},
        ]

        for i, a in enumerate(alunos_docs, start=1):
            u, _ = User.objects.get_or_create(
                username=a['user'],
                defaults={'first_name': a['nome'].split()[0], 'is_aluno': True}
            )
            u.set_password('aluno123')
            u.save()

            t_obj = Turma.objects.filter(
                nome=a['turma'],
                classe=a['classe'],
                curso=cursos_info[a['curso']]
            ).first()

            if t_obj:
                num_proc = f"2026{i:04d}"
                Aluno.objects.get_or_create(
                    usuario=u,
                    defaults={'turma': t_obj, 'numero_processo': num_proc}
                )
                self.stdout.write(f"  ✔ {a['nome']} → {t_obj}")
            else:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠️  Turma não encontrada para {a['nome']} (classe={a['classe']}, curso={a['curso']}, turma={a['turma']})"
                ))

        # --- 6. SUPERUSUÁRIO ---
        self.stdout.write("🔐 Verificando Superusuário...")
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@tarimba.co.ao',
                password='Cratos123'
            )
            self.stdout.write(self.style.SUCCESS("  ✔ Superusuário criado: admin / tarimba@admin2026"))
        else:
            self.stdout.write("  ℹ️  Superusuário já existe, ignorado.")

        self.stdout.write(self.style.SUCCESS("✅ Sistema Tarimba Totalmente Povoado com Sucesso!"))