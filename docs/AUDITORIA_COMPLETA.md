# COLA-ZERO - Auditoria Completa do Projeto

**Data da auditoria:** 18 de agosto de 2026  
**Escopo:** leitura dos documentos `.md`, inspeção do backend e frontend, e validação automatizada local

## 1. Objetivo

Este documento consolida o resultado da auditoria do projeto COLA-ZERO com foco em:

1. O que já está implementado no backend.
2. O que já está implementado no frontend.
3. O que ainda falta implementar ou consolidar.

## 2. Fontes consultadas

Documentos de referência lidos antes da inspeção do código:

- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [STATUS_ATUAL.md](../STATUS_ATUAL.md)
- [ROADMAP.md](../ROADMAP.md)
- [README.md](../README.md)
- [PLANO_AVALIACOES.md](../PLANO_AVALIACOES.md)
- [PLANO_BANCO_QUESTOES.md](../PLANO_BANCO_QUESTOES.md)
- [PLANO_OMR.md](../PLANO_OMR.md)
- [PLANO_DASHBOARD.md](../PLANO_DASHBOARD.md)
- [PLANO_ANTI_COLA.md](../PLANO_ANTI_COLA.md)
- [PLANO_MODELO_ACADEMICO.md](../PLANO_MODELO_ACADEMICO.md)
- [TARGET_DOMAIN_MODEL.md](../TARGET_DOMAIN_MODEL.md)
- [docs/STEP_1_POST_IMPLEMENTATION_AUDIT.md](STEP_1_POST_IMPLEMENTATION_AUDIT.md)

Validação executada na auditoria:

- Backend: `175 passed`
- Frontend: `22 passed`

## 3. Resumo executivo

O projeto está em um estado avançado e funcional.

O backend cobre os pilares centrais do COLA-ZERO:

- autenticação e RBAC;
- modelo acadêmico de turmas e vínculos;
- Banco de Questões;
- avaliações online com entrega sequencial e autosave;
- AnswerKey como núcleo do domínio;
- OMR para provas impressas;
- relatórios e exportações;
- auditoria, consentimentos e LGPD básica.
- solicitação de anonimização com revisão administrativa antes da execução.

O frontend já expõe as principais jornadas de uso para professor, estudante e administrador, com páginas reais para:

- login, sessão por cookie HttpOnly e criação administrativa de usuários;
- dashboard;
- turmas;
- questões;
- avaliações;
- tentativa online;
- OMR;
- revisão de scans.

O principal ponto de atenção da auditoria é este:

- a base técnica está ampla e funcional;
- o backend cobre o núcleo do produto;
- a interface ainda precisa fechar alguns fluxos operacionais, principalmente a padronização das confirmações destrutivas e a consolidação final da experiência administrativa.

## 4. O que já está implementado no backend

### 4.1 Autenticação, usuários e RBAC

Implementado e testado:

- login;
- criação administrativa de usuários em `/admin/users`;
- refresh token;
- endpoint `me`;
- atualização de perfil;
- proteção por `get_current_user` e `require_role`;
- perfis `student`, `teacher` e `admin`.

Arquivos principais:

- [backend/app/api/routes/auth.py](../backend/app/api/routes/auth.py)
- [backend/app/services/auth.py](../backend/app/services/auth.py)
- [backend/app/core/security.py](../backend/app/core/security.py)

### 4.2 Modelo acadêmico de turmas

Implementado:

- criação de turmas;
- listagem;
- detalhe da turma;
- arquivamento;
- vínculo de professores;
- vínculo de estudantes;
- histórico de matrícula;
- checagem de acesso por associação explícita.

Arquivos principais:

- [backend/app/api/routes/classes.py](../backend/app/api/routes/classes.py)
- [backend/app/services/class_service.py](../backend/app/services/class_service.py)
- [backend/app/models/class_.py](../backend/app/models/class_.py)

### 4.3 Banco de Questões

Implementado:

- modelo de questão reutilizável;
- vínculo com habilidades;
- criação de questão;
- listagem com busca, filtro e paginação;
- criação de habilidades.

O que existe no modelo:

- versionamento por `parent_id` e `version`;
- `is_active`;
- associação com `skills`.

Limite observado:

- a API pública ainda expõe apenas criação, listagem e consulta de questões;
- não há, nesta auditoria, endpoints de edição/versionamento explícito, nem fluxo de exclusão lógica pela API.

Arquivos principais:

- [backend/app/api/routes/questions.py](../backend/app/api/routes/questions.py)
- [backend/app/api/routes/skills.py](../backend/app/api/routes/skills.py)
- [backend/app/repositories/question.py](../backend/app/repositories/question.py)
- [backend/app/models/question.py](../backend/app/models/question.py)

### 4.4 Avaliações e AnswerKey

Implementado:

- criação de avaliações;
- publicação e retorno para rascunho;
- arquivamento;
- atualização;
- estatísticas;
- exportação em PDF;
- exportação em XLSX;
- pré-visualização;
- integração com turmas;
- Workflow A e Workflow B no backend;
- AnswerKey como fonte canônica de correção.

Também está implementado:

- sincronização de `exam_classes`;
- materialização de `AnswerKey` a partir de perguntas;
- materialização direta de `AnswerKey` a partir de respostas manuais.

Arquivos principais:

- [backend/app/api/routes/exams.py](../backend/app/api/routes/exams.py)
- [backend/app/services/exam.py](../backend/app/services/exam.py)
- [backend/app/services/answer_key.py](../backend/app/services/answer_key.py)
- [backend/app/models/answer_key.py](../backend/app/models/answer_key.py)

### 4.5 Tentativas online

Implementado:

- lista de provas disponíveis ao estudante;
- início da tentativa;
- leitura da questão atual;
- salvamento imediato da resposta;
- navegação para próxima e anterior;
- submissão final;
- consulta do resultado;
- controle por status da tentativa;
- limite de tentativas;
- correção baseada em AnswerKey.

Arquivos principais:

- [backend/app/api/routes/attempts.py](../backend/app/api/routes/attempts.py)
- [backend/app/services/attempt.py](../backend/app/services/attempt.py)
- [backend/app/models/attempt.py](../backend/app/models/attempt.py)

### 4.6 OMR

Implementado:

- criação de template OMR;
- listagem;
- detalhe;
- geração de PDF;
- geração de preview PNG;
- upload de imagem;
- upload em lote;
- revisão manual de scan;
- confirmação da correção;
- persistência em `grades`.

O módulo OMR está coerente com o princípio de prova impressa, e a correção depende do gabarito da avaliação.

Arquivos principais:

- [backend/app/api/routes/omr.py](../backend/app/api/routes/omr.py)
- [backend/app/services/omr.py](../backend/app/services/omr.py)
- [backend/app/core/omr_layouts.py](../backend/app/core/omr_layouts.py)

### 4.7 Dashboard, relatórios e exportações

Implementado no backend:

- estatísticas por prova;
- análise por questão;
- exportação PDF;
- exportação XLSX;
- base de dados para dashboard pedagógico;
- integração com `grades`, `attempts`, `skills` e `answer_key`.

Arquivos principais:

- [backend/app/api/routes/exams.py](../backend/app/api/routes/exams.py)
- [backend/app/services/export.py](../backend/app/services/export.py)

### 4.8 LGPD, auditoria e integridade

Implementado:

- política de privacidade;
- exportação de dados do usuário;
- solicitação de anonimização com fila administrativa;
- revisão administrativa do pedido antes da execução da anonimização;
- consentimentos;
- consentimento de monitoramento;
- eventos de segurança por tentativa;
- trilha de auditoria.

Arquivos principais:

- [backend/app/api/routes/privacy.py](../backend/app/api/routes/privacy.py)
- [backend/app/api/routes/consents.py](../backend/app/api/routes/consents.py)
- [backend/app/api/routes/security_events.py](../backend/app/api/routes/security_events.py)
- [backend/app/api/routes/audit_logs.py](../backend/app/api/routes/audit_logs.py)

## 5. O que já está implementado no frontend

### 5.1 Acesso e navegação base

Implementado:

- página inicial com redirecionamento;
- login;
- área administrativa de cadastro de usuários;
- proteção de rota;
- contexto de autenticação com sessão por cookie HttpOnly.

Arquivos principais:

- [frontend/app/page.tsx](../frontend/app/page.tsx)
- [frontend/app/auth/login/page.tsx](../frontend/app/auth/login/page.tsx)
- [frontend/app/admin/users/page.tsx](../frontend/app/admin/users/page.tsx)
- [frontend/app/components/ProtectedRoute.tsx](../frontend/app/components/ProtectedRoute.tsx)

### 5.2 Dashboard

Implementado:

- painel de controle por perfil;
- entrada para provas online;
- entrada para turmas;
- entrada para OMR;
- entrada para avaliações e relatórios.

Arquivo principal:

- [frontend/app/dashboard/page.tsx](../frontend/app/dashboard/page.tsx)

### 5.3 Avaliações

Implementado:

- listagem de avaliações;
- criação de avaliação com seleção de questões;
- integração com turmas;
- publicação;
- exportação PDF;
- exportação XLSX;
- página de detalhe com estatísticas;
- pré-visualização;
- geração de pacote OMR.

Arquivos principais:

- [frontend/app/exams/page.tsx](../frontend/app/exams/page.tsx)
- [frontend/app/exams/new/page.tsx](../frontend/app/exams/new/page.tsx)
- [frontend/app/exams/[examId]/page.tsx](../frontend/app/exams/[examId]/page.tsx)

### 5.4 Tentativa online

Implementado:

- seleção de prova disponível;
- início de tentativa por prova;
- tela de questão única por vez;
- navegação anterior e próxima;
- autosave no fluxo visual;
- submissão e visualização de resultado.

Arquivos principais:

- [frontend/app/attempts/start/page.tsx](../frontend/app/attempts/start/page.tsx)
- [frontend/app/attempts/[attemptId]/page.tsx](../frontend/app/attempts/[attemptId]/page.tsx)

### 5.5 OMR

Implementado:

- listagem de gabaritos;
- criação de gabarito OMR;
- detalhe com download do PDF;
- preview PNG;
- upload simples;
- upload em lote;
- revisão de scan;
- confirmação de nota.

Arquivos principais:

- [frontend/app/omr/page.tsx](../frontend/app/omr/page.tsx)
- [frontend/app/omr/new/page.tsx](../frontend/app/omr/new/page.tsx)
- [frontend/app/omr/[templateId]/page.tsx](../frontend/app/omr/[templateId]/page.tsx)
- [frontend/app/omr/scans/[scanId]/page.tsx](../frontend/app/omr/scans/[scanId]/page.tsx)

### 5.6 Turmas e banco de questões

Implementado:

- listagem de turmas;
- criação de turma;
- detalhe da turma;
- vínculo e remoção de professores e estudantes;
- listagem de questões;
- criação de questão;
- criação de habilidade;
- busca e filtros.

Arquivos principais:

- [frontend/app/classes/page.tsx](../frontend/app/classes/page.tsx)
- [frontend/app/classes/[classId]/page.tsx](../frontend/app/classes/[classId]/page.tsx)
- [frontend/app/questions/page.tsx](../frontend/app/questions/page.tsx)

## 6. O que falta implementar ou consolidar

### 6.1 Fluxo de mobilidade acadêmica

Falta consolidar o fluxo de movimentação de aluno entre turmas:

- transferência atômica de um aluno de uma turma para outra;
- UI específica para esse movimento, sem depender de remover e readicionar manualmente;
- registro de auditoria mais explícito da troca de turma;
- reforço visual de que o aluno só pode estar ativo em uma turma por período.

Situação atual:

- a regra de uma matrícula ativa por período já é aplicada no backend;
- o backend já permite criar turma vazia e depois vincular professores/alunos;
- a UI da turma já expõe transferência individual e promoção em lote para migração anual;

### 6.2 Confirmações destrutivas e UX administrativa

Algumas ações sensíveis ainda precisam de padronização visual e de cópia:

- arquivamento de turma;
- arquivamento de avaliação;
- inativação de questão;
- exclusão de gabarito OMR;
- harmonização da linguagem de risco em todas as telas administrativas.

Situação atual:

- a tela de usuários já possui confirmação explícita de inativação e exclusão;
- outras telas ainda executam ações destrutivas com menos contexto do que o ideal.

### 6.3 LGPD e anti-cola no frontend

O backend já expõe os recursos, e a interface já cobre a base de privacidade e consentimentos, mas ainda pode evoluir em:

- tela pública de política de privacidade;
- fluxo mais explícito de consentimento antes da prova online;
- visualização de consentimentos do usuário;
- tela administrativa para eventos de segurança;
- tela administrativa para revisão de solicitações de anonimização.
- revisão pedagógica de eventos suspeitos;
- painéis mais claros para o monitoramento de integridade.

### 6.4 Analytics e dashboard avançado

O núcleo de relatório existe, mas ainda há espaço para:

- gráficos mais ricos;
- exploração visual por habilidade;
- visões comparativas mais completas;
- refinamento da UX administrativa;
- melhor apresentação dos dados de exportação.

### 6.5 OMR avançado

O OMR já está funcional, mas ainda faltam evoluções de escala e robustez:

- processamento em lote de PDFs multipágina;
- abstração de storage mais madura para cenários distribuídos;
- eventual expansão além dos layouts padrão de 10 a 100 questões.

### 6.6 Hardening operacional

Ainda é recomendável consolidar:

- refinamento dos avisos de ambiente e dependências;
- documentação operacional do fluxo de deploy;
- monitoramento de regressões em testes com maior granularidade;
- tratamento explícito dos arquivos locais não versionados no repositório.

## 7. Validação realizada

### Backend

Resultado:

- `175 passed`
- `100 warnings`

Observações:

- houve warning de depreciação entre `httpx` e `starlette.testclient`;
- houve warning de dependência circular ao destruir tabelas em testes;
- nenhum desses avisos impediu a validação.

### Frontend

Resultado:

- `22 passed`

Observações:

- os testes foram verdes;
- a suíte usa mocks em várias rotas e serviços, o que é adequado para isolamento de interface.

## 8. Conclusão

O COLA-ZERO está em estado funcional consistente e com o núcleo do produto implementado.

O backend atende os pilares do domínio e o frontend já cobre as jornadas principais de uso.

O que ainda falta não é a fundação do sistema, e sim a consolidação de camadas específicas:

- confirmações destrutivas consistentes em todas as áreas administrativas;
- analytics mais profundo;
- OMR em lote multipágina e storage abstrato;
- refinamentos finais de UX em telas densas.

Em termos práticos:

- o projeto já funciona;
- a base arquitetural está madura;
- a próxima prioridade é fechar as lacunas de operação, governança e experiência de uso.

## 9. Checklist Priorizado de Pendências

### P0 - Alta prioridade

- [x] Padronizar confirmações destrutivas para arquivar turma, arquivar avaliação, inativar questão e excluir gabarito OMR.
- [x] Criar um atalho operacional para a promoção anual dos alunos sem depender de remoção e re-vinculação manual.

### P1 - Prioridade média

- [ ] Ampliar a camada visual de analytics pedagógico com gráficos mais ricos e leitura por habilidade.
- [ ] Melhorar os detalhes de turma e usuário para leitura operacional mais clara.
- [ ] Refinar a tela pública de privacidade e os fluxos de consentimento antes das provas online.
- [ ] Expor visualização mais legível dos eventos de segurança, consentimentos e solicitações de anonimização no frontend administrativo.

### P2 - Prioridade baixa

- [ ] Evoluir a abstração de storage para OMR com foco em escalabilidade horizontal.
- [ ] Expandir o processamento OMR para PDFs multipágina em lote.
- [ ] Revisar a cobertura de testes de integração para os fluxos mais sensíveis.
- [ ] Preparar melhoria visual e de navegação para painéis administrativos menos usados no dia a dia.

## 10. Plano de Execução por Etapas

### Etapa 1 - Fechar a base funcional

**Objetivo:** completar as lacunas que impedem o ciclo de manutenção e governança de ficar totalmente fechado.

**Entregas:**

- fluxo completo de edição/versionamento do Banco de Questões exposto na API;
- inativação/exclusão lógica de questões;
- tela e API de política de privacidade, consentimento e solicitação de anonimização mais explícitas para o usuário;
- visão administrativa dos eventos de segurança, consentimentos e solicitações de anonimização.

**Critério de saída:**

- o acervo de questões pode ser criado, consultado, versionado e inativado sem depender de caminho manual;
- o fluxo de consentimento fica visível e rastreável;
- o administrador consegue auditar os eventos sensíveis.

#### Tarefas técnicas

1. Mapear o ciclo atual do Banco de Questões.
   - confirmar quais endpoints existem hoje;
   - confirmar como o `Question` versionado é persistido;
   - confirmar se há back-end service pronto para edição/inativação.
2. Implementar a edição/versionamento da questão.
   - criar o endpoint de update;
   - garantir que a edição gere nova versão quando a regra exigir imutabilidade;
   - preservar o histórico da versão anterior.
3. Implementar a inativação lógica da questão.
   - expor `PATCH` ou `DELETE` lógico;
   - bloquear uso futuro de versões inativas;
   - manter a leitura histórica intacta.
4. Fechar o fluxo de consentimento no frontend.
   - expor a política de privacidade de forma acessível;
   - registrar consentimento de monitoramento antes da prova;
   - mostrar o estado atual do consentimento ao usuário.
5. Fechar a visão administrativa de LGPD e integridade.
   - criar tela para consultar consentimentos;
   - criar tela ou seção para consultar eventos de segurança;
   - manter filtros básicos por usuário/tipo/evento.

#### Sequência sugerida

1. Começar pelo backend do Banco de Questões.
   - a base técnica do versionamento e da inativação precisa existir antes da interface;
   - sem essa camada, o frontend ficaria acoplado a uma regra incompleta.
2. Fechar os endpoints de LGPD e integridade no backend.
   - política de privacidade;
   - exportação de dados;
   - consentimento de monitoramento;
   - listagem de eventos de segurança.
3. Subir a interface administrativa do Banco de Questões.
   - edição;
   - nova versão;
   - inativação;
   - confirmação visual do histórico.
4. Subir a interface de LGPD e auditoria.
   - consentimentos do usuário;
   - política pública;
   - leitura administrativa dos eventos sensíveis.
5. Validar a ponta a ponta.
   - criar caso de teste para versão nova de questão;
   - criar caso de teste para inativação;
   - criar caso de teste para consentimento e exportação;
   - criar caso de teste para consulta de eventos de segurança.

### Etapa 2 - Consolidar a experiência de uso

**Objetivo:** melhorar a utilidade diária das áreas já implementadas.

**Entregas:**

- analytics pedagógico com visualizações mais ricas;
- navegação mais clara para exportações PDF/XLSX;
- revisão manual de OMR com feedback mais consistente;
- refinamento do fluxo de criação de avaliações entre questões, turmas e publicação.

**Critério de saída:**

- o professor consegue operar provas, relatórios e OMR com menos fricção;
- as telas principais ficam mais previsíveis e informativas;
- a leitura pedagógica do sistema fica mais clara.

#### Tarefas técnicas

1. Melhorar a navegação das avaliações.
   - revisar a tela de listagem;
   - revisar o detalhe com estatísticas;
   - padronizar ações de publicar, arquivar e exportar.
2. Reforçar a criação de provas.
   - reduzir passos desnecessários na seleção de questões;
   - melhorar feedback quando não houver turmas ou questões suficientes;
   - revisar a consistência entre o que é criado no backend e o que a tela mostra.
3. Melhorar o fluxo OMR.
   - tornar a revisão manual mais clara;
   - destacar status do scan e erro;
   - facilitar a confirmação de nota.
4. Evoluir analytics e dashboard.
   - priorizar visualizações por habilidade;
   - organizar métricas gerais por turma e prova;
   - deixar exportações mais fáceis de localizar.

#### Sequência sugerida

1. Primeiro estabilizar a tela de detalhe da avaliação.
   - ela concentra publicação, retorno para rascunho, arquivamento e exportações;
   - é a principal tela de operação para o professor.
2. Depois melhorar a criação de avaliação.
   - reduzir retrabalho ao montar a prova;
   - deixar mais clara a relação entre questões, turmas e publicação.
3. Em seguida ajustar a revisão OMR.
   - o fluxo de scan precisa ficar mais legível e confiável;
   - confirmação de nota e correção manual devem ficar mais explícitas.
4. Por fim, ampliar dashboard e relatórios.
   - essa camada agrega valor, mas depende do núcleo operacional já consistente.

### Etapa 3 - Escala e hardening

**Objetivo:** preparar o sistema para crescimento e reduzir dependências frágeis.

**Entregas:**

- abstração de storage para OMR compatível com escala horizontal;
- suporte ampliado a novos layouts OMR;
- endurecimento dos testes de integração dos fluxos críticos;
- tratamento dos warnings e ajustes operacionais do ambiente.

**Critério de saída:**

- o sistema tolera expansão sem depender tanto do filesystem local;
- a manutenção de novos formatos OMR deixa de exigir intervenção manual frequente;
- a base de testes e operação fica mais robusta.

#### Tarefas técnicas

1. Trocar o storage local por uma abstração formal.
   - definir interface de storage;
   - manter backend local para desenvolvimento;
   - preparar backend compatível com MinIO/object storage.
2. Expandir layouts OMR.
   - revisar registry atual;
   - adicionar novos layouts sem quebrar os existentes;
   - validar impacto em PDF, preview e engine.
3. Endurecer a suíte de testes.
   - reforçar cenários de integração críticos;
   - separar testes de backend, frontend e fluxo completo;
   - revisar warnings recorrentes.
4. Ajustar operação e documentação.
   - registrar dependências obrigatórias e opcionais;
   - documentar comandos de execução mais estáveis;
   - apontar limitações conhecidas do ambiente local.

#### Sequência sugerida

1. Definir a interface de storage.
   - esta é a base para trocar a implementação sem afetar OMR.
2. Adaptar a implementação local atual.
   - manter compatibilidade com o comportamento existente.
3. Adicionar backend alternativo compatível com object storage.
   - isso prepara o caminho para escala horizontal.
4. Expandir layouts OMR em paralelo com testes.
   - cada novo layout precisa de validação no PDF, preview e engine.
5. Consolidar hardening operacional.
   - ajustar warnings;
   - documentar dependências;
   - atualizar evidências de validação.
