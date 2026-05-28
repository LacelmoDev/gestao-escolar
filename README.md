# Sistema de Gestão Académica Integrada
### Colégio Tarimba — C.E.P. J.M.F.D - Calumbo

---

## Sobre o Projecto

O **Sistema Tarimba** é uma plataforma web desenvolvida como Projecto de Aptidão Profissional (PAP) pelos alunos da **13ª Classe do Curso Técnico de Informática de Gestão** do Complexo Escolar Privado J.M.F.D Tarimba, no ano lectivo 2025/2026.

O sistema digitaliza e automatiza os processos de gestão académica do colégio, substituindo os registos manuais em papel por uma solução moderna, segura e acessível a partir de qualquer dispositivo.

---

## Demonstração Online

```
https://tarimba.onrender.com/
```

---

## Funcionalidades

### Para Candidatos (visitantes)
- Submissão de inscrição online com upload de documentos
- Validação automática de combinação classe/curso
- Validação de data de nascimento
- Comprovativo de inscrição em PDF
- Emails automáticos a cada etapa do processo

### Para Alunos
- Dashboard com notas trimestrais (MAC, NPP, NPT) e médias
- Controlo de faltas com estado (justificada, em análise, não justificada)
- Submissão de justificativas com documento anexo
- Histórico por ano lectivo
- Edição de perfil

### Para Professores
- Dashboard com turmas atribuídas
- Lançamento e actualização de notas por trimestre
- Registo de faltas
- Aprovação/rejeição de justificativas de faltas

### Para Administradores
- Gestão completa de inscrições com fluxo de 3 acções
- Criação automática de alunos e credenciais de acesso
- Envio automático de emails em cada etapa
- Gestão de turmas, disciplinas, professores e atribuições
- Relatórios e estatísticas

---

## Tecnologias Utilizadas

| Componente | Tecnologia |
|---|---|
| Framework | Django 6.0.5 (Python) |
| Base de Dados | PostgreSQL (Render) |
| Frontend | Tailwind CSS + HTML5 + JavaScript |
| Servidor | Gunicorn |
| Hospedagem | Render.com |
| Emails | Brevo (API HTTP) |
| Ficheiros | Cloudinary |
| Autenticação | Django Auth |

---

## Fluxo de Inscrição

```
Candidato submete formulário
        ↓
   [Email: Inscrição Recebida]
        ↓
Admin executa Acção 1 — Confirmar Dados
        ↓
   [Email: Dados Confirmados — ir pagar]
        ↓
Candidato paga presencialmente no colégio
        ↓
Admin executa Acção 2 — Validar Pagamento
        ↓
   [Email: Boas-vindas com credenciais de acesso]
        ↓
Aluno acede ao Portal com login = Nº BI
```

Em qualquer etapa antes do pagamento, o admin pode executar a **Acção 3 — Rejeitar**, que notifica o candidato por email.

---

## Como Executar Localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/teu-user/tarimba_project.git
cd tarimba_project
```

### 2. Criar e activar ambiente virtual
```bash
python -m venv .venv

# Linux / Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
Cria um ficheiro `.env` na raiz do projecto com as seguintes variáveis:

```
SECRET_KEY=gera-uma-chave-segura-aqui
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

EMAIL_HOST_PASSWORD=a-tua-api-key-brevo
EMAIL_HOST_USER=o-teu-email-brevo
DEFAULT_FROM_EMAIL=Colegio Tarimba <o-teu-email>

CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

> Para gerar uma SECRET_KEY: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 5. Aplicar migrações e popular dados iniciais
```bash
python manage.py migrate
python manage.py povoar
```

### 6. Iniciar o servidor
```bash
python manage.py runserver
```

### 7. Aceder no browser
```
http://127.0.0.1:8000/
```

---

## Estrutura do Projecto

```
tarimba_project/
├── core/               # Configurações globais e URLs
├── usuarios/           # Modelo de utilizador personalizado
├── escola/             # Cursos, turmas, disciplinas, professores
│   └── management/
│       └── commands/
│           └── povoar.py   # Comando de dados iniciais
├── academico/          # Inscrições, alunos, notas, presenças
├── templates/          # Templates HTML
├── static/             # CSS, JS, imagens
├── requirements.txt
└── .env                # Nunca commitar este ficheiro
```

---

## Segurança

- Painel admin em URL não-padrão (obscurecido)
- Protecção CSRF com `CSRF_TRUSTED_ORIGINS`
- Validação de dados no frontend (JS) e backend (Django forms)
- Passwords armazenadas com hash PBKDF2
- Variáveis sensíveis em ambiente, nunca no código
- `DEBUG=False` em produção

---

## Equipa

* Lacelmo Carlos

---

## Licença / Termos de Uso

Todos os direitos reservados. Este software é proprietário e confidencial. 
A cópia, modificação, distribuição ou uso comercial deste código, no todo 
ou em parte, são estritamente proibidos sem a autorização prévia e por 
escrito do autor.
