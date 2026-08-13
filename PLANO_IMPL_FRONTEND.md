# COLA-ZERO - Plano de Implementacao do Frontend

> Documento de planejamento do frontend apos a reorganizacao visual das areas de portal, academia, administracao, OMR, questoes e tentativas.

---

## 1. Objetivo

Consolidar a experiencia de interface do COLA-ZERO em um conjunto coerente de shells, telas operacionais e fluxos de usuario, reduzindo duplicacao de navegacao e tornando as principais jornadas mais claras.

---

## 2. Estado Atual

Ja foram consolidados:

- portal principal com navegacao unificada;
- area academica com shell compartilhado;
- area administrativa com shell compartilhado;
- fluxo de tentativas do aluno com shell proprio;
- paginas de `dashboard`, `consents`, `privacy`, `classes`, `exams`, `questions` e `omr` sem chrome duplicado.

Ainda existem pendencias de produto e UX, principalmente em:

- busca global;
- dashboard administrativo com dados reais;
- confirmacoes de acao destrutiva;
- movimentacao de aluno entre turmas;
- detalhes mais completos de usuarios e turmas;
- refinamento responsivo das telas densas.

---

## 3. Checklist Priorizado

### P0 - Critico

1. Tornar a busca global funcional ou remove-la ate existir uma implementacao confiavel.
2. Substituir os dados mockados do dashboard admin por dados reais.
3. Padronizar confirmacoes para exclusao, arquivamento e inativacao.
4. Criar fluxo claro para mover aluno de turma, garantindo a regra de uma turma por vez.
5. Melhorar estados vazios e mensagens de orientacao nas telas operacionais.

### P1 - Importante

1. Criar paginas de detalhe mais completas para usuarios e turmas no admin.
2. Padronizar modais, alerts e feedback visual em todo o frontend.
3. Revisar a leitura da home do portal para cada perfil de usuario.
4. Melhorar responsividade das telas densas de questoes, avaliacoes e tentativas.

### P2 - Evolucao

1. Reduzir repeticao visual com componentes reutilizaveis.
2. Refinar microcopy para acoes sensiveis e LGPD.
3. Fazer uma ultima passada de consistencia entre portal, area academica, admin e tentativas.

---

## 4. Plano de Implementacao

### Fase 1 - Base de Interacao

Entregas:

- implementar busca global com comportamento util;
- substituir alertas soltos por confirmacoes e modais padronizados;
- remover ou desativar entradas visuais que nao tenham acao real;
- definir componentes basicos para feedback de sucesso, erro e confirmacao.

Aceite:

- nenhuma acao critica fica sem aviso claro;
- a busca global tem comportamento definido;
- o usuario entende o impacto da acao antes de executar.

### Fase 2 - Admin Operacional

Entregas:

- substituir mock data do dashboard admin por dados reais;
- criar pagina de detalhe de usuario com dados, vinculos e acoes;
- criar pagina de detalhe de turma com membros, professores e historico;
- expor trilha de auditoria mais legivel para alteracoes sensiveis.

Aceite:

- admin consegue localizar um usuario ou turma sem depender apenas de listas;
- as principais acoes ficam a um clique do contexto correto;
- o dashboard admin deixa de ser demonstrativo e passa a ser operacional.

### Fase 3 - Mobilidade Academica

Entregas:

- implementar transferencia de aluno entre turmas;
- reforcar a regra de uma turma por vez para aluno;
- permitir turma vazia como estado valido desde a criacao;
- tratar desativacao e arquivamento sem quebrar os vinculos restantes.

Aceite:

- o ciclo anual de mover alunos entre turmas funciona sem trabalho manual excessivo;
- a turma pode existir vazia;
- o sistema explica o efeito da mudanca antes de executa-la.

### Fase 4 - Consistencia de Produto

Entregas:

- revisar estados vazios e copy em questoes, avaliacoes e OMR;
- ajustar responsividade nas telas mais densas;
- uniformizar hierarquia visual entre listas, detalhes e formulários;
- revisar home do portal para manter foco por papel de usuario.

Aceite:

- as telas principais mantem boa leitura em desktop e mobile;
- os estados vazios orientam o proximo passo;
- a navegação entre areas nao parece fragmentada.

### Fase 5 - Fechamento

Entregas:

- revisar regressões com build e testes focados;
- atualizar os documentos de status e roadmap com o que foi concluido;
- registrar os itens ainda pendentes para a proxima iteracao.

Aceite:

- o frontend continua compilando;
- os documentos refletem o estado real do projeto;
- o backlog restante fica claro e priorizado.

---

## 5. Ordem Recomendada de Execucao

1. Busca global e feedback padronizado.
2. Dashboard admin com dados reais.
3. Detalhes de usuario e turma.
4. Fluxo de mover aluno entre turmas.
5. Revisao visual de questoes, avaliacoes, OMR e tentativas.

---

## 6. Criterios de Conclusao da Iteracao

Este plano pode ser considerado avancado quando:

- o portal principal tiver navegacao util para cada papel;
- o admin tiver contexto operacional real, nao apenas listas;
- a movimentacao de alunos entre turmas estiver resolvida;
- o frontend mantiver build verde;
- a documentacao refletir o estado final da interface.

