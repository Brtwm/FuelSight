# FuelSight: развертывание на REG.RU VPS

Инструкция рассчитана на первый production-запуск FuelSight с полным Airflow,
сгенерированными demo-данными и обязательным cloud LLM. Локальный `.env` не
изменяется и не коммитится.

## 1. Что заказать в REG.RU

Рекомендуемая конфигурация:

- Ubuntu 24.04 LTS без ISPmanager;
- 4 vCPU;
- 8 GB RAM;
- не менее 80 GB SSD;
- публичный IPv4;
- отдельный домен или поддомен для FuelSight.

После создания сервера сохраните его IP. В панели DNS создайте `A`-запись,
направленную на этот IP. Обновление DNS может занять до 24 часов:

<https://help.reg.ru/support/dns-servery-i-nastroyka-zony/rabota-s-dns-serverami/kak-privyazat-domen-k-ip-adresu>

Проверка с локального компьютера:

```powershell
Resolve-DnsName fuelsight.example.com
```

В результате должен появиться IP нового VPS.

## 2. Первый вход и отдельный deploy-пользователь

Добавьте SSH public key при создании VPS. Первый вход:

```powershell
ssh root@VPS_IP
```

На сервере:

```bash
adduser deploy
usermod -aG sudo deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
```

Откройте вторую локальную консоль и убедитесь, что вход работает:

```powershell
ssh deploy@VPS_IP
```

Только после успешной проверки создайте `/etc/ssh/sshd_config.d/99-fuelsight.conf`:

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Проверка и применение:

```bash
sudo sshd -t
sudo systemctl reload ssh
```

Не закрывайте текущую SSH-сессию, пока не проверен новый вход.

## 3. Firewall и базовая защита

```bash
sudo apt update
sudo apt install -y ufw fail2ban unattended-upgrades ca-certificates curl gnupg nginx certbot python3-certbot-nginx
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
sudo systemctl enable --now fail2ban
```

Если у вас постоянный IP, замените `ufw allow OpenSSH` правилом только для него.

## 4. Docker Engine

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker deploy
```

Выйдите из SSH, войдите снова и проверьте:

```bash
docker version
docker compose version
```

## 5. Каталоги production

```bash
sudo install -d -m 750 -o deploy -g deploy \
  /opt/fuelsight/compose/init \
  /opt/fuelsight/compose/env \
  /opt/fuelsight/compose/nginx \
  /opt/fuelsight/env \
  /opt/fuelsight/scripts \
  /opt/fuelsight/backups
```

## 6. Подготовка production.env

На Windows в корне локального проекта:

```powershell
.\scripts\prepare-production-env.ps1
```

Скрипт:

- только читает локальный `.env`;
- копирует LLM/API values без изменения;
- создает новые JWT/PostgreSQL/Airflow secrets;
- сохраняет результат в игнорируемый `env/production.env`;
- не выводит секреты в консоль.

Проверьте только список ключей, не печатая значения:

```powershell
Get-Content .\env\production.env |
  Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } |
  ForEach-Object { ($_ -split '=', 2)[0] }
```

Передайте файл напрямую:

```powershell
scp .\env\production.env deploy@VPS_IP:/opt/fuelsight/env/production.env
ssh deploy@VPS_IP "chmod 600 /opt/fuelsight/env/production.env"
```

Не добавляйте этот файл в GitHub Secrets и не коммитьте его.

## 7. Домен, nginx и HTTPS

Сначала создайте временную HTTP-конфигурацию на VPS:

```bash
sudo tee /etc/nginx/sites-available/fuelsight >/dev/null <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name ВАШ_ДОМЕН;

    location / {
        proxy_pass http://127.0.0.1:3000;
        include proxy_params;
    }
}
NGINX
sudo ln -s /etc/nginx/sites-available/fuelsight /etc/nginx/sites-enabled/fuelsight
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
sudo certbot certonly --nginx -d ВАШ_ДОМЕН
```

После выпуска сертификата скопируйте полный nginx template:

```powershell
scp .\compose\nginx\fuelsight.conf.example deploy@VPS_IP:/tmp/fuelsight.conf
```

На VPS:

```bash
sed -i 's/fuelsight\.example\.com/ВАШ_ДОМЕН/g' /tmp/fuelsight.conf
sudo cp /tmp/fuelsight.conf /etc/nginx/sites-available/fuelsight
sudo nginx -t
sudo systemctl reload nginx
sudo certbot renew --dry-run
```

## 8. GitHub Environment

В GitHub откройте `Settings → Environments → New environment` и создайте
`production`. Включите required reviewer для ручного подтверждения.

Добавьте secrets:

- `VPS_HOST` — IP или домен;
- `VPS_USER` — `deploy`;
- `VPS_PORT` — обычно `22`;
- `VPS_SSH_PRIVATE_KEY` — отдельный deploy private key;
- `VPS_SSH_KNOWN_HOSTS` — результат локального `ssh-keyscan -H VPS_IP`;
- `GHCR_USERNAME` — GitHub username;
- `GHCR_READ_TOKEN` — fine-grained token только с `read:packages`.

LLM, JWT и database secrets в GitHub не добавляются.

## 9. Первый publish и deploy

После merge в `main`:

1. дождитесь успешных `CI` и `Security`;
2. workflow `Publish production images` создаст три GHCR image с тегом commit SHA;
   frontend image собирается через `frontend/Dockerfile.production`, а локальный
   Vite-based `frontend/Dockerfile` остается без изменений; production Airflow
   собирается на поддерживаемой ветке 3.2 через
   `backend/airflow/Dockerfile.production`;
3. запустите `Deploy production`;
4. укажите полный 40-символьный SHA;
5. подтвердите deployment в environment `production`.

Проверка на VPS:

```bash
cd /opt/fuelsight
IMAGE_TAG="$(cat .release)"
export IMAGE_TAG
docker compose \
  --env-file env/production.env \
  -f compose/docker-compose.production.yml ps
curl -fsS http://127.0.0.1:3000/api/v1/health
```

`db` и `backend` не должны иметь host ports. `frontend` и Airflow привязаны
только к `127.0.0.1`.

## 10. Генерация данных, модели, новостей и RAG

Один раз после первого deploy:

```bash
cd /opt/fuelsight
IMAGE_TAG="$(cat .release)" ./scripts/bootstrap-production.sh
```

Команда последовательно выполняет migrations, seed ролей/продуктов, генерацию
годовой истории, live external ingest, feature store, CatBoost training,
backtest, live news refresh и RAG indexing. Все результаты сохраняются в
persistent volumes.

## 11. Reviewer-пользователи

```bash
cd /opt/fuelsight
export IMAGE_TAG="$(cat .release)"

docker compose --env-file env/production.env \
  -f compose/docker-compose.production.yml run --rm backend \
  fuelsight-create-reviewer \
  --email analyst-review@example.com \
  --display-name "Аналитик — комиссия" \
  --role analyst

docker compose --env-file env/production.env \
  -f compose/docker-compose.production.yml run --rm backend \
  fuelsight-create-reviewer \
  --email director-review@example.com \
  --display-name "Директор — комиссия" \
  --role director
```

Пароли вводятся интерактивно, не отображаются и не сохраняются в shell history.

## 12. Production smoke и LLM

Проверьте:

```bash
curl -fsS https://ВАШ_ДОМЕН/api/v1/health
curl -I https://ВАШ_ДОМЕН
```

Затем войдите как `analyst`, откройте `/news`, создайте chat session и задайте
вопрос по последним новостям. В diagnostics должны быть:

- `enable_llm=true`;
- `llm_provider=neuraldeep`;
- `mode=cloud_llm`;
- непустой список citations.

При недоступности provider допустим только явно показанный `retrieval_only`
fallback с citations.

## 13. Airflow через SSH tunnel

На локальном компьютере:

```powershell
ssh -L 8080:127.0.0.1:8080 deploy@VPS_IP
```

Откройте <http://127.0.0.1:8080>. Порт `8080` не должен открываться напрямую
через публичный IP.

## 14. Backup, restore и rollback

Ручной backup:

```bash
/opt/fuelsight/scripts/backup-production.sh
ls -lh /opt/fuelsight/backups
```

Проверка restore в отдельную временную базу:

```bash
cd /opt/fuelsight
export IMAGE_TAG="$(cat .release)"
LATEST_BACKUP="$(ls -1t backups/fuelsight-*.sql.gz | head -n 1)"

docker compose --env-file env/production.env \
  -f compose/docker-compose.production.yml exec -T db \
  sh -c 'dropdb --if-exists -U "$POSTGRES_USER" fuelsight_restore_test &&
         createdb -U "$POSTGRES_USER" fuelsight_restore_test'

gzip -dc "$LATEST_BACKUP" | \
  docker compose --env-file env/production.env \
    -f compose/docker-compose.production.yml exec -T db \
    sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" fuelsight_restore_test'

docker compose --env-file env/production.env \
  -f compose/docker-compose.production.yml exec -T db \
  sh -c 'dropdb -U "$POSTGRES_USER" fuelsight_restore_test'
```

Не выполняйте restore-проверку поверх рабочей базы `fuelsight`.

Ежедневный cron:

```bash
crontab -e
```

```cron
15 2 * * * /opt/fuelsight/scripts/backup-production.sh >>/opt/fuelsight/backups/backup.log 2>&1
```

Deploy автоматически возвращает предыдущие application images при провале
health-check. Миграции базы автоматически назад не откатываются; перед каждой
миграцией создается dump.

Проверка логов:

```bash
cd /opt/fuelsight
export IMAGE_TAG="$(cat .release)"
docker compose --env-file env/production.env \
  -f compose/docker-compose.production.yml logs --tail=200 backend
```

## 15. Финальная проверка перед QR-кодом

- URL открывается с телефона через мобильный интернет;
- сертификат валиден;
- `analyst` видит analytics, forecast, news и cited chat;
- `director` видит executive dashboard/report;
- imports/admin routes недоступны reviewer-ролям;
- после `docker compose restart` данные и модель сохраняются;
- публичные `5432`, `8061`, `8080` закрыты;
- GitHub `CI`, `Security`, image scan и Production DAST успешны.
