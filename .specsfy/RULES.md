# Regras do sistema

Estas regras complementam as instruções dos agentes sem substituir specs ou
critérios de aceite. Modelo inicial sugerido para **stack ainda não identificado**.

Confirme os manifests e as fronteiras principais antes de completar o modelo genérico.

## Arquitetura

- Estruturar a lógica de negócio com orientação a objetos, encapsulamento, módulos focados, alta coesão e baixo acoplamento; scripts procedurais ficam limitados a ferramentas pontuais.

- Usar Factory ou Adapter para criação de providers, Strategy para comportamentos que variam por contexto e Repository para isolar regras de negócio do acesso à persistência.

- Implementar toda nova orquestração de IA com LangGraph v1+ e componentes LangChain v1+; qualquer alternativa exige justificativa escrita antes da implementação.

## Código e qualidade

- Criar e usar uma branch própria para cada fase de desenvolvimento; não trabalhar diretamente na branch principal.

- Executar Ruff e a suíte Pytest antes de integrar este componente ao projeto-mãe.

- Usar Specsfy como workflow normativo único deste repositório; manter backlog, especificação, gates e tarefas nos caminhos canônicos do framework e não criar plan.md, tasks.md ou artefatos paralelos do GitHub SpecKit.

## Testes

- Executar Pytest antes de integrar mudanças; componentes críticos devem seguir Red-Green-Refactor, com testes escritos antes da implementação.

## Segurança e privacidade

- Nunca versionar ou expor credenciais, senhas, tokens ou configuração sensível; manter segredos fora do repositório e centralizar o acesso à configuração.

## Operação

## Regras específicas do projeto
