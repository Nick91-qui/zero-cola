# COLA-ZERO — Plano de Execução Prático da Milestone 1

## 1. Objetivo da milestone

Entregar o primeiro fluxo funcional do MVP com os seguintes resultados:

- professor autentica
- professor cria questões
- professor cria prova
- aluno autentica
- aluno inicia tentativa
- backend entrega uma questão por vez
- aluno envia respostas sequencialmente
- respostas ficam persistidas com segurança

Escopo principal desta milestone:

- fundação técnica do backend e frontend
- PostgreSQL e migrações
- autenticação JWT
- RBAC básico
- CRUD inicial de questões
- criação e publicação de provas
- início de tentativa
- próxima questão
- submissão de resposta

## 2. Critério de pronto da milestone

A milestone é considerada pronta quando:

- backend e frontend sobem localmente
- autenticação funciona com JWT
- RBAC bloqueia acessos indevidos
- professor consegue criar e consultar questões
- professor consegue criar, compor e publicar prova
- aluno consegue iniciar tentativa
- backend entrega apenas a questão atual
- resposta é persistida imediatamente após envio

## 3. Ordem operacional recomendada

### Bloco 1 — Fundação do backend

Issues:

- `ISSUE-001`
- `ISSUE-002`
- `ISSUE-003`

Objetivo:

Criar a base técnica do backend, conexão com banco e suporte a migrações.

Saída esperada:

- app FastAPI funcional
- healthcheck disponível
- conexão com PostgreSQL funcionando
- Alembic configurado e pronto para novas migrations

Risco principal:

- atrasos por configuração inicial inconsistente entre app, banco e migration

Checklist do bloco:

- [ ] FastAPI sobe localmente
- [ ] PostgreSQL conecta com sucesso
- [ ] migration inicial executa upgrade e downgrade

### Bloco 2 — Identidade e segurança base

Issues:

- `ISSUE-004`
- `ISSUE-005`
- `ISSUE-006`
- `ISSUE-007`
- `ISSUE-008`

Objetivo:

Entregar a fundação de autenticação e autorização do sistema.

Saída esperada:

- tabela `users`
- hash de senha seguro
- geração e validação de JWT
- login e refresh implementados
- RBAC aplicável aos endpoints seguintes

Risco principal:

- implementar autenticação sem definir claramente o fluxo de sessão e renovação

Checklist do bloco:

- [ ] usuário autentica com sucesso
- [ ] refresh token funciona
- [ ] endpoints protegidos retornam erro de permissão quando necessário

### Bloco 3 — Fundação do frontend de autenticação

Issues:

- `ISSUE-009`
- `ISSUE-010`
- `ISSUE-011`

Objetivo:

Entregar a base do frontend e permitir login funcional.

Saída esperada:

- frontend Next.js funcional
- página de login conectada ao backend
- sessão persistida no frontend

Risco principal:

- desalinhamento entre formato dos tokens, estratégia de persistência e proteção de acesso

Checklist do bloco:

- [ ] frontend sobe localmente
- [ ] login funciona pela interface
- [ ] sessão autenticada é mantida conforme regra definida

### Bloco 4 — Modelo central do domínio

Issues:

- `ISSUE-012`
- `ISSUE-013`
- `ISSUE-016`
- `ISSUE-017`

Objetivo:

Criar a base do domínio de questões, provas, vínculos e tentativas.

Saída esperada:

- tabelas centrais do domínio criadas
- schemas de `Question` e `Exam` definidos
- relação `ExamQuestion` funcionando

Risco principal:

- schema divergir do `DATABASE.MD` e do princípio de reutilização de questões

Checklist do bloco:

- [ ] tabelas principais existem no banco
- [ ] relacionamento `Exam -> ExamQuestion -> Question` funciona
- [ ] prova não depende de cópia de conteúdo da questão

### Bloco 5 — Banco de questões

Issues:

- `ISSUE-014`
- `ISSUE-015`

Objetivo:

Permitir gestão inicial do banco de questões por professor.

Saída esperada:

- CRUD básico de questões
- filtros por disciplina, dificuldade e tags

Risco principal:

- mistura de regra de autorização com lógica de listagem e filtros

Checklist do bloco:

- [ ] professor cria questão
- [ ] professor lista questões
- [ ] filtros funcionam corretamente
- [ ] aluno não acessa a gestão de questões

### Bloco 6 — Provas

Issues:

- `ISSUE-018`

Objetivo:

Permitir criação, composição e publicação de provas.

Saída esperada:

- professor cria prova
- professor associa questões à prova
- professor publica prova

Risco principal:

- permitir publicação de prova inconsistente ou sem composição válida

Checklist do bloco:

- [ ] prova é criada como `draft`
- [ ] questões são associadas com ordem e peso
- [ ] publicação funciona com validações mínimas

### Bloco 7 — Attempt Engine mínimo

Issues:

- `ISSUE-019`
- `ISSUE-020`
- `ISSUE-021`

Objetivo:

Entregar o núcleo operacional da aplicação: tentativa, próxima questão e submissão de resposta.

Saída esperada:

- tentativa pode ser criada
- backend retorna apenas a questão atual
- resposta é persistida imediatamente

Risco principal:

- quebrar a regra central de uma questão por vez

Checklist do bloco:

- [ ] tentativa inicia com estado válido
- [ ] endpoint de próxima questão retorna somente uma questão
- [ ] resposta fica gravada logo após o envio

### Bloco 8 — Interface de tentativa

Issues:

- `ISSUE-022`

Objetivo:

Fechar o fluxo da milestone pela interface do aluno.

Saída esperada:

- aluno responde a prova em fluxo sequencial
- frontend consome `next-question` e `answers`

Risco principal:

- frontend antecipar estado da prova sem depender do backend

Checklist do bloco:

- [ ] página de tentativa renderiza a questão atual
- [ ] envio de resposta funciona
- [ ] próxima questão é carregada em sequência

## 4. Validação mínima por etapa

### Após bloco 2

Executar um teste manual simples:

- criar usuário de teste
- realizar login
- validar emissão de tokens
- validar acesso negado em endpoint protegido sem permissão

### Após bloco 5

Executar um teste manual simples:

- autenticar como professor
- criar questões
- consultar listagem
- aplicar filtros

### Após bloco 6

Executar um teste manual simples:

- criar prova
- adicionar questões
- publicar prova

### Após bloco 8

Executar um teste manual ponta a ponta:

- autenticar professor
- criar questão
- criar e publicar prova
- autenticar aluno
- iniciar tentativa
- responder sequência de questões
- confirmar persistência das respostas no banco

## 5. Dependências críticas

Dependências que não devem ser quebradas:

- `ISSUE-001 -> ISSUE-002 -> ISSUE-003`
- `ISSUE-004 -> ISSUE-005 -> ISSUE-006 -> ISSUE-007 -> ISSUE-008`
- `ISSUE-012 -> ISSUE-013 -> ISSUE-014 -> ISSUE-015`
- `ISSUE-012 -> ISSUE-016 -> ISSUE-017 -> ISSUE-018`
- `ISSUE-018 -> ISSUE-019 -> ISSUE-020 e ISSUE-021 -> ISSUE-022`

## 6. Estratégia de implementação sugerida

### Estratégia por ramo de trabalho

Sugestão de agrupamento por branch:

- branch 1: fundação backend e banco
- branch 2: autenticação e RBAC
- branch 3: frontend de login e sessão
- branch 4: banco de questões e provas
- branch 5: attempt engine e tela de tentativa

### Estratégia por integração

Após cada bloco:

- revisar contratos de API
- revisar permissões
- executar testes disponíveis
- validar manualmente o fluxo entregue

## 7. Riscos e decisões que devem ser resolvidas cedo

### Sessão do frontend

Definir cedo:

- onde access token e refresh token serão mantidos
- como será feita renovação de sessão
- como proteger rotas no Next.js

### Publicação de prova

Definir cedo:

- regras mínimas para publicar uma prova
- se é obrigatório ter ao menos uma questão
- se ordem e peso são obrigatórios sempre

### Início de tentativa

Definir cedo:

- qual endpoint cria a tentativa
- quando uma tentativa pode ser iniciada
- como impedir múltiplas tentativas inválidas, se aplicável ao MVP

## 8. Entregável final esperado

Ao final da milestone 1, o repositório deve estar pronto para demonstrar o seguinte cenário:

1. professor faz login
2. professor cria questões
3. professor cria e publica uma prova
4. aluno faz login
5. aluno inicia tentativa
6. sistema entrega uma questão por vez
7. aluno responde
8. respostas são persistidas com segurança

Esse é o primeiro recorte funcional real do COLA-ZERO.