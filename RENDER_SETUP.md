# Guia de Deploy no Render

## 1. Variáveis de Ambiente Obrigatórias

Configure as seguintes variáveis no painel do Render (Settings → Environment):

```env
ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<uma-chave-secreta-aleatoria-longa>
DATABASE_URL=<sua-url-postgresql-ou-mysql>

# Cloudinary (para upload de mídia)
CLOUD_NAME_DO_CLOUDINARY=<seu-cloud-name>
API_KEY_DO_CLOUDINARY=<sua-api-key>
API_SECRET_DO_CLOUDINARY=<seu-api-secret>

# Email (Gmail ou outro SMTP)
EMAIL_HOST_USER=<seu-email@gmail.com>
EMAIL_HOST_PASSWORD=<sua-senha-app>

# CSRF e HOSTS - Substitua <seu-app> pelo domínio real do seu app Render
ALLOWED_HOSTS=<seu-app>.onrender.com
CSRF_TRUSTED_ORIGINS=https://<seu-app>.onrender.com
```

### Exemplo completo:
Se sua app Render é `https://tarimba-xyz.onrender.com`:

```env
ALLOWED_HOSTS=tarimba-xyz.onrender.com
CSRF_TRUSTED_ORIGINS=https://tarimba-xyz.onrender.com
```

**⚠️ IMPORTANTE:** 
- `CSRF_TRUSTED_ORIGINS` **OBRIGATORIAMENTE** inclui `https://`
- `ALLOWED_HOSTS` **NÃO** inclui `https://`, apenas o domínio
- Sem espaços extras após vírgulas

## 2. Build Command (opcional, caso queira customizar)

Default no Render:
```bash
pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

Ou configure no arquivo `render.yaml` se preferir.

## 3. Start Command

Default:
```bash
gunicorn core.wsgi:application
```

Se tiver `Procfile`, configure como:
```
web: gunicorn core.wsgi:application
```

## 4. Debug do CSRF 403

Se receber **Proibido (403) Verificação CSRF falhou**:

### a) Verificar cookie no navegador
1. Abra DevTools (F12)
2. Vá em **Application → Cookies**
3. Procure por cookie `csrftoken`
4. Se existir, note o valor

### b) Testar manualmente via curl

```bash
# 1. Fazer GET da página e salvar cookies
curl -c cookies.txt -L https://<seu-app>.onrender.com/inscrever/ > /dev/null

# 2. Extrair token CSRF
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
echo "Token CSRF: $CSRF"

# 3. Fazer POST com o token
curl -b cookies.txt -X POST https://<seu-app>.onrender.com/inscrever/ \
  -H "X-CSRFToken: $CSRF" \
  -F "nome_completo=Teste Silva" \
  -F "data_nascimento=2005-01-01" \
  -F "genero=M" \
  -F "bi_numero=000000000" \
  -F "telefone=999123456" \
  -F "email=teste@example.com" \
  -F "curso_pretendido=1" \
  -F "classe_pretendida=10" \
  -v
```

### c) Verificar logs no Render
- Painel Render → Seu app → Logs
- Procure por erros relacionados a `CSRF` ou `ALLOWED_HOSTS`

### d) Causas comuns e soluções

| Problema | Solução |
|----------|---------|
| "CSRF token missing" | Certifique-se que `{% csrf_token %}` está no template (já está em `form_inscricao.html`) |
| "CSRF token incorrect" ou "CSRF token verification failed" | `CSRF_TRUSTED_ORIGINS` não inclui `https://` ou domínio está errado |
| Cookie não aparece em DevTools | `CSRF_COOKIE_SECURE=True` pode estar bloqueando; verificar se site é HTTPS |
| Referer inválido | O navegador pode estar bloqueando referer; testar com `-H "Referer: https://<seu-app>.onrender.com/inscrever/"` no curl |

## 5. Confirmar Deploy Bem-Sucedido

Após fazer deploy, teste:

```bash
# Verificar migração de DB
curl -I https://<seu-app>.onrender.com/admin/

# Acessar página de inscrição
curl -I https://<seu-app>.onrender.com/inscrever/

# Se ambas retornam 200 ou 302, tudo bem-configurado
```

## 6. Environment Variables via .env.example

Para referência local, use o arquivo `.env.example` como template:

```bash
cp .env.example .env  # somente em desenvolvimento
```

**Nunca comite `.env` com valores reais ao GitHub!**

---

## Resumo Rápido

1. **Discover seu domínio Render** → `https://<seu-app>.onrender.com`
2. **Configure variáveis de ambiente** no painel Render
3. **Redeploy** e teste o formulário
4. **Se CSRF 403 persistir**, use o debug via curl para diagnosticar

Qualquer dúvida, verifique os logs em **Render → Logs**.
