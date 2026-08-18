# COLA-ZERO — Plano de Implementacao da Tela Admin

> **Single Source of Truth** para a sequencia de implementacao da nova area administrativa do COLA-ZERO.
>
> Este plano transforma o desenho funcional de [PLANO_TELA_ADMIN.md](PLANO_TELA_ADMIN.md) em entregas implementaveis, priorizadas e testaveis.

---

## 1. Objetivo da Implementacao

Construir uma experiencia administrativa consistente, navegavel e operavel para que o admin consiga:

1. chegar rapidamente a usuarios, turmas, auditoria, consentimentos e privacidade;
2. executar criacao, inativacao, arquivamento e remocao de vinculos com contexto claro;
3. entender o estado do sistema sem depender de menus soltos;
4. manter o historico academico e de governanca legivel.

---

## 2. Escopo desta Implementacao

### 2.1 Inclui

- shell administrativo compartilhado com sidebar e topbar;
- pagina inicial do admin como dashboard operacional;
- adaptacao das paginas de usuarios e auditoria ao novo shell;
- padrao visual base para evolucao futura de turmas, privacidade e consentimentos;
- documentacao do novo fluxo.

### 2.2 Nao inclui nesta fase

- pagina dedicada de detalhe de usuario;
- pagina dedicada de detalhe de turma;
- drawers de acao rapida;
- filtros avancados em todas as listas;
- rotas novas para `admin/privacy` e `admin/consents`.

---

## 3. Sequencia de Entrega

### Fase 1 — Base Visual Compartilhada

Entregas:

- criar um shell administrativo reutilizavel;
- adicionar sidebar com rotas principais;
- adicionar topbar com identidade, busca visual e logout;
- destacar a secao ativa da navegação.

Critério de aceite:

- todas as paginas admin existentes usam o mesmo envelope visual;
- o usuario reconhece claramente onde esta;
- o layout reduz a necessidade de repetir navegacao em cada pagina.

### Fase 2 — Visao Geral Administrativa

Entregas:

- reorganizar `/admin` como dashboard de operacao;
- expor metricas resumidas;
- mostrar alertas prioritarios;
- mostrar acoes recentes;
- exibir atalhos diretos para as jornadas mais frequentes.

Critério de aceite:

- a tela inicial responde rapidamente ao que esta acontecendo;
- o admin consegue ir para a acao sem percorrer paginas secundarias.

### Fase 3 — Usuarios

Entregas:

- alinhar a pagina de usuarios ao novo shell;
- manter criacao restrita;
- manter filtros e lista operacional;
- preservar confirmacoes para inativacao e exclusao;
- reforcar estados de vinculo com turmas.

Critério de aceite:

- o admin consegue localizar, criar e ajustar usuarios sem perder contexto.

### Fase 4 — Auditoria

Entregas:

- alinhar a pagina de auditoria ao novo shell;
- manter logs administrativos visiveis;
- manter consulta por tentativa online;
- destacar eventos sensiveis.

Critério de aceite:

- auditoria fica acessivel a partir da area administrativa principal sem ruído visual.

### Fase 5 — Turmas e Governança

Entregas futuras:

- aplicar a mesma linguagem visual em `/classes`;
- criar pontos de entrada para privacidade e consentimentos dentro do shell;
- criar paginas administrativas de detalhe para usuarios e turmas.

Critério de aceite:

- a navegacao principal da administracao fica completa e consistente.

---

## 4. Regras de UX que Devem Ser Mantidas

1. Separar claramente informacao, navegacao e acao.
2. Preferir tabelas e listas para gestao operacional.
3. Usar cards apenas para resumo ou atalhos.
4. Exibir avisos claros para arquivar, inativar e excluir.
5. Tratar turma sem professor como estado valido.
6. Preservar historico ao modificar vinculos.

---

## 5. Prioridades Tecnicas

### P0

- extrair o shell admin compartilhado;
- padronizar a navegação;
- remover duplicacao de header nas paginas admin.

### P1

- revisar copy e ordem dos blocos na home admin;
- refinar a pagina de usuarios com foco em leitura rapida;
- ajustar a pagina de auditoria para hierarquia melhor.

### P2

- consolidar paginas de detalhe;
- unificar a experiencia de turmas, privacidade e consentimentos.

---

## 6. Verificacao

A implementacao deve ser considerada fechada quando:

- o build do frontend concluir sem erro;
- a navegação admin estiver consistente em desktop;
- nao existir duplicacao de shell entre as paginas do admin;
- as paginas de usuarios e auditoria continuarem funcionais;
- o layout inicial da nova area estiver documentado.
