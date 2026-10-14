# Labels do Traefik para o Beta

Consulta: 2026-10-13. Fontes oficiais Traefik Proxy v2.11. Resumo próprio,
sem reprodução integral. A versão instalada na VPS ainda não foi inspecionada;
os nomes confirmados do resolvedor e do entrypoint continuam os da spec.

## Swarm

Fonte: https://doc.traefik.io/traefik/v2.11/providers/docker/

Em Swarm, as labels pertencem ao serviço (`deploy.labels`). A porta do backend
precisa ser declarada por `loadbalancer.server.port`; o frontend usa 3000.
Cada roteador aponta explicitamente para o mesmo serviço de balanceamento.
Nenhum proxy é criado por esta entrega.

## Redirecionamento

Fonte: https://doc.traefik.io/traefik/v2.11/middlewares/http/redirectscheme/

`redirectscheme.scheme=https` com `permanent=true` redireciona HTTP.
O middleware fica só no roteador HTTP, evitando laço no HTTPS. O entrypoint
HTTP `web` permanece uma suposição a conferir na VPS.

## HSTS

Fonte: https://doc.traefik.io/traefik/v2.11/middlewares/http/headers/

`headers.stsSeconds` controla max-age em segundos; zero omite o cabeçalho.
Usar 86400 inicialmente, sem subdomínios nem preload. Aplicar o middleware
nos dois roteadores HTTPS, inclusive login e respostas recusadas pelo limite.

## Limite de tentativas

Fonte: https://doc.traefik.io/traefik/v2.11/middlewares/http/ratelimit/

A taxa é average/period; declarar `period=1m`, pois o padrão é um segundo.
Average 10 e burst 20 são os valores iniciais da spec. Sem header de origem
nem requestHost, o agrupamento usa o endereço remoto; depth zero evita confiar
em X-Forwarded-For fornecido pelo cliente. A suposição é ausência de CDN.
O efeito 429 exige a conferência real na VPS; labels não provam o tráfego.

## Prioridade

Fonte: https://doc.traefik.io/traefik/v2.11/routing/routers/

Sem prioridade explícita, vale o comprimento da regra. Usar prioridade 10
no geral e 100 no login, cuja regra inclui Host, Method POST e Path exato.
O login aplica cabeçalhos antes do limite; o geral aplica apenas cabeçalhos.

## Divergências e limites

Nenhuma mudança de comportamento necessária. A unidade da média precisa ser
explícita. A versão e o entrypoint HTTP reais devem ser conferidos em T027.
Traefik v3 separa o provider Swarm do Docker; estas labels HTTP não introduzem
referências com sufixo de provider e usam a rede única já declarada no stack.
