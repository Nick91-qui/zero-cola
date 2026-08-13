# COLA-ZERO — Plano de Design da Tela Admin

> **Single Source of Truth** para o desenho funcional e visual da área administrativa do COLA-ZERO.
>
> Este documento define a estrutura da interface, a hierarquia de navegação, os componentes principais e os estados da tela admin com base nas necessidades reais do projeto.

---

## 1. Objetivo

Redesenhar a experiência administrativa para que o admin consiga:

1. localizar usuários rapidamente;
2. criar professores e alunos com os vínculos corretos;
3. gerenciar turmas, professores e alunos sem ambiguidade;
4. consultar auditoria, consentimentos e privacidade;
5. executar ações perigosas com confirmação explícita;
6. entender o estado do sistema sem depender de telas “decorativas” ou menus soltos.

---

## 2. Princípios de Design

### 2.1 Navegação primeiro

- A interface deve reduzir a quantidade de cliques para chegar a usuário, turma ou evento.
- A navegação principal deve ser sempre visível.
- A home do admin deve orientar, não competir com as páginas operacionais.

### 2.2 Operação antes de estética

- A tela admin é uma ferramenta de trabalho.
- A legibilidade e a velocidade de leitura têm prioridade sobre ornamentos.
- O visual pode ser refinado, mas nunca pode esconder fluxo ou ação.

### 2.3 Ações críticas exigem contexto

- Excluir, arquivar, inativar e remover vínculo precisam de aviso explícito.
- Toda ação destrutiva deve informar impacto, reversibilidade e efeito colateral.
- Sempre que possível, priorizar arquivamento/inativação em vez de exclusão física.

### 2.4 Estado vazio é um estado de trabalho

- Turmas podem nascer sem professor.
- Usuários podem existir sem vínculo imediato com turma.
- A UI deve tratar “vazio” como passo intermediário legítimo, não como erro.

### 2.5 Histórico preservado

- O design deve refletir que o sistema preserva histórico.
- Trocar aluno de turma não deve parecer uma edição destrutiva do passado.
- A tela precisa comunicar claramente a diferença entre vínculo ativo, arquivado e histórico.

---

## 3. Necessidades do Projeto que a Tela Deve Cobrir

### 3.1 Identidade e acesso

- criação de professor, aluno e admin por fluxo restrito;
- visualização de status da conta;
- inativação, arquivamento e eventual anonimização;
- busca por email, matrícula ou papel.

### 3.2 Turmas

- criação de turma vazia;
- vínculo posterior de professores;
- vínculo posterior de alunos;
- indicação clara de turma sem professor;
- troca de aluno de turma com preservação histórica;
- arquivamento e eventual exclusão com aviso forte.

### 3.3 Auditoria e LGPD

- leitura de eventos sensíveis;
- estados de consentimento;
- política de privacidade;
- exportação e anonimização de dados.

### 3.4 Consolidação operacional

- visão rápida do que está ativo;
- alertas de atenção imediata;
- atalhos para tarefas frequentes;
- rastreabilidade do que mudou recentemente.

---

## 4. Estrutura de Navegação Recomendada

### 4.1 Layout Base

- `Sidebar fixa` para navegação principal.
- `Topbar` com busca global, usuário logado e logout.
- `Área central` com lista, detalhe ou dashboard.
- `Painel lateral opcional` para ações rápidas e detalhes.

### 4.2 Itens da Sidebar

Prioridade sugerida:

1. `Visão geral`
2. `Usuários`
3. `Turmas`
4. `Auditoria`
5. `Consentimentos`
6. `Privacidade`
7. `Configurações`

### 4.3 Rotas sugeridas

- `/admin` -> visão geral
- `/admin/users` -> lista operacional de usuários
- `/admin/users/[id]` -> detalhe do usuário
- `/admin/classes` -> lista operacional de turmas
- `/admin/classes/[id]` -> detalhe da turma
- `/admin/audit` -> auditoria e eventos sensíveis
- `/admin/consents` -> consentimentos
- `/admin/privacy` -> política e exportação

---

## 5. Estrutura da Tela Inicial

### 5.1 Função da home

A tela inicial do admin deve responder três perguntas:

1. O que está acontecendo?
2. O que precisa de atenção?
3. Onde eu entro agora?

### 5.2 Blocos principais

- cartões de métricas resumidas;
- alertas prioritários;
- ações recentes;
- atalhos rápidos.

### 5.3 O que a home não deve ser

- não deve virar um mural de botões;
- não deve repetir a navegação principal;
- não deve substituir as páginas de gestão.

---

## 6. Página de Usuários

### 6.1 Objetivo

Dar ao admin uma lista clara e rápida de todas as contas.

### 6.2 Componentes

- busca por email, matrícula ou papel;
- filtros por status, papel e vínculo;
- tabela com colunas de interesse operacional;
- ações por linha;
- detalhe expandido ou página dedicada.

### 6.3 Colunas recomendadas

- email;
- papel;
- status;
- turma(s) vinculada(s);
- último acesso ou atividade relevante;
- ações.

### 6.4 Ações recomendadas

- ver detalhe;
- criar vínculo;
- inativar;
- reativar;
- anonimizar, quando aplicável;
- excluir apenas se houver política explícita para isso.

---

## 7. Página de Turmas

### 7.1 Objetivo

Permitir controle rápido de turmas, professores e alunos.

### 7.2 Componentes

- busca por nome, período ou descrição;
- filtros por período e status;
- tabela operacional;
- detalhe da turma;
- ações administrativas com confirmação.

### 7.3 Colunas recomendadas

- nome da turma;
- período;
- professores vinculados;
- alunos ativos;
- status;
- ações.

### 7.4 Estados importantes

- turma ativa;
- turma arquivada;
- turma sem professor;
- turma sem alunos;
- turma com vínculos históricos, mas sem vínculos ativos.

### 7.5 Fluxos críticos

#### Criar turma vazia

- a turma pode ser criada sem professor;
- depois o admin vincula professores e alunos.

#### Vincular professor

- adicionar primeiro professor;
- manter histórico dos vínculos anteriores;
- mostrar se o professor é o responsável atual apenas como metadado, não como dono exclusivo.

#### Trocar aluno de turma

- remover vínculo atual e adicionar novo vínculo como fluxo guiado;
- exibir aviso de que o histórico será preservado;
- aplicar regra de uma turma ativa por período.

#### Arquivar turma

- arquivar deve ser preferido antes de exclusão;
- alertar que vínculos e histórico permanecem;
- impedir edição irrestrita após arquivamento.

#### Excluir turma

- só como ação excepcional;
- mostrar alerta explícito de impacto;
- exigir confirmação mais forte que a de arquivamento.

---

## 8. Página de Detalhe da Turma

### 8.1 Estrutura sugerida

- cabeçalho com nome, período e status;
- resumo com contagem de professores e alunos;
- bloco de professores vinculados;
- bloco de alunos vinculados;
- ações administrativas.

### 8.2 Informações que precisam ficar claras

- se a turma está ativa ou arquivada;
- se não há professor vinculado;
- quais vínculos são ativos;
- qual vínculo é histórico;
- quem pode editar aquela turma.

### 8.3 Ações recomendadas no detalhe

- vincular professor;
- remover vínculo de professor;
- vincular aluno;
- remover vínculo de aluno;
- mover aluno para outra turma;
- arquivar turma;
- excluir turma.

---

## 9. Página de Auditoria

### 9.1 Objetivo

Expor os eventos sensíveis de forma legível e auditável.

### 9.2 Componentes

- busca;
- filtros por evento, usuário e período;
- tabela com carimbo temporal;
- detalhe do evento quando necessário.

### 9.3 Colunas recomendadas

- data e hora;
- tipo de evento;
- usuário responsável;
- recurso afetado;
- resultado;
- referência para detalhe.

---

## 10. Privacidade e Consentimentos

### 10.1 Privacidade

- política vigente;
- exportação de dados;
- solicitação de anonimização;
- status do atendimento.

### 10.2 Consentimentos

- consentimento de monitoramento;
- estado por usuário;
- histórico de revogações;
- marcação clara de quem concedeu, revogou e quando.

---

## 11. Linguagem Visual Recomendada

### 11.1 Direção geral

- interface limpa;
- baixo ruído visual;
- foco em informação e ação;
- hierarquia clara;
- aparência de console administrativa, não de landing page.

### 11.2 Paleta e estado

- neutros para fundo e containers;
- uma cor de ação primária;
- amarelo/laranja para atenção;
- vermelho para ações destrutivas;
- verde apenas para status positivo.

### 11.3 Componentes

- cards enxutos;
- tabelas com densidade boa;
- chips de status;
- modais de confirmação;
- drawers ou páginas de detalhe para ações secundárias.

### 11.4 Evitar

- textura pesada;
- decoração com pouca função;
- blocos visuais com mesmo peso para tudo;
- ações destrutivas sem confirmação;
- “cards de menu” como navegação principal.

---

## 12. Responsividade

### 12.1 Desktop

- sidebar fixa;
- tabelas completas;
- detalhe lateral ou página dedicada;
- filtros no topo da lista.

### 12.2 Tablet

- sidebar colapsável;
- tabelas com menos colunas visíveis;
- ações agrupadas em menu.

### 12.3 Mobile

- menu em drawer;
- listas em cards compactos ou tabela simplificada;
- ações principais por item;
- detalhe por página.

---

## 13. Acessibilidade e Clareza

- contraste suficiente entre texto e fundo;
- labels explícitos;
- botões com verbos claros;
- estados vazios com próxima ação sugerida;
- confirmação textual para ações perigosas;
- foco visível e navegação por teclado.

---

## 14. Prioridade de Implementação

### P0

- sidebar fixa;
- visão geral administrativa;
- lista de usuários;
- lista de turmas;
- detalhe da turma;
- confirmação de ações destrutivas;
- tratamento de turma sem professor.

### P1

- busca global;
- filtros avançados;
- detalhe do usuário;
- auditoria operacional;
- consentimentos e privacidade em páginas próprias.

### P2

- drawers de ação rápida;
- atalhos contextuais;
- estados vazios mais ricos;
- refinamento visual progressivo.

---

## 15. Critérios de Aceitação do Design

O design da tela admin deve ser considerado adequado quando:

1. o admin encontra usuários e turmas sem depender de vários cliques;
2. o estado “turma sem professor” é compreensível e acionável;
3. arquivar, excluir e inativar têm diferença visual e semântica clara;
4. os vínculos de professor e aluno são legíveis;
5. auditoria e consentimentos são acessíveis sem poluir a navegação principal;
6. a home não compete com as páginas operacionais;
7. a interface permanece útil em telas menores;
8. o layout não depende de ornamentos para ser compreendido.

---

## 16. Referências de Base

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [STATUS_ATUAL.md](STATUS_ATUAL.md)
- [ROADMAP.md](ROADMAP.md)
- [PLANO_MODELO_ACADEMICO.md](PLANO_MODELO_ACADEMICO.md)
- [docs/AUDITORIA_COMPLETA.md](docs/AUDITORIA_COMPLETA.md)
- [proposta-de-tela-2.png](proposta-de-tela-2.png)
