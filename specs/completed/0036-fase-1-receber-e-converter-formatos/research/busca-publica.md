# Evidências para busca de páginas públicas

Consultado em 2026-10-15. Material informativo da SPEC-0036, FR-002/NFR-001.

- OWASP, SSRF Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html — publicação sob CC BY-SA 4.0. A orientação fundamenta a validação de cada endereço DNS, a conexão ao endereço validado e a validação explícita de redirecionamentos. Não basta validar um nome e deixar o cliente resolvê-lo novamente.
- Python 3.12, http.client: https://docs.python.org/3.12/library/http.client.html — documentação PSF. HTTPConnection/HTTPSConnection oferecem requisição e leitura de resposta; HTTPS mantém verificação do certificado e hostname. A implementação mantém o host original na conexão TLS e usa um socket ligado diretamente ao IP aprovado. Nenhum proxy de ambiente é utilizado.

Amostras HTTP e DNS dos testes são sintéticas; nenhuma página real foi consultada como dado de cliente.
