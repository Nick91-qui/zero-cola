# COLA-ZERO — Plano de Implementação: Produção e Visualização de Provas

> **Single Source of Truth** para o próximo passo funcional do fluxo de avaliações: separar a criação de questões da montagem da prova, permitir a visualização da prova antes da publicação e gerar folhas OMR personalizadas por aluno para impressão.
>
> **Estado atual**: esta fase foi implementada e validada. A pré-visualização da prova, a montagem por seleção de questões, a consulta do Banco de Questões e a exportação de folhas OMR personalizadas por aluno já estão disponíveis no backend e no frontend.

---

## 1. Objetivo Funcional

O objetivo desta etapa é transformar a produção de provas em um fluxo explícito e rastreável:

1. o professor consulta o Banco de Questões;
2. o professor seleciona questões já existentes para montar uma prova;
3. o sistema compõe a visualização da prova e o `AnswerKey` correspondente;
4. o sistema gera folhas OMR personalizadas para os alunos vinculados às turmas da prova;
5. o fluxo mantém compatibilidade com Workflow A, Workflow B, tentativas online e correção OMR.

---

## 2. Escopo da Implementação

### 2.1 Consulta e Seleção de Questões
- O professor deve poder listar, filtrar e visualizar questões reutilizáveis do Banco de Questões.
- A visualização deve mostrar enunciado, alternativas, habilidades associadas e status da questão.
- A seleção de questões para uma prova deve ocorrer fora da criação da prova em si.

### 2.2 Montagem da Prova
- A prova deve ser criada como um container de avaliação separado do conteúdo das questões.
- O professor deve selecionar questões já existentes no Banco de Questões.
- A ordem, o peso e a composição da prova devem ser configuráveis.
- A publicação deve continuar materializando o `AnswerKey` a partir das questões selecionadas.

### 2.3 Visualização da Prova
- A pré-visualização da prova montada já está implementada.
- A visualização não expõe a resposta correta para o estudante.
- A tela de visualização destaca a composição da prova, quantidade de questões, pesos e habilidades.

### 2.4 Geração de Folhas OMR Personalizadas
- O sistema deve gerar uma folha de resposta por aluno elegível.
- Cada folha deve vir com os dados do aluno preenchidos automaticamente.
- A geração deve considerar as turmas às quais a prova foi atribuída.
- O layout OMR atual deve continuar sendo resolvido pelo backend, sem alterar a lógica de correção.

### 2.5 Regra de Separação de Responsabilidades
- Criação de questões não deve ocorrer dentro do fluxo de criação de prova.
- A prova passa a selecionar questões do Banco de Questões.
- O OMR continua sendo apenas o canal físico de correção.

---

## 3. Checklist de Implementação

### 3.1 Banco de Questões consultável
- [x] Expor listagem de questões com filtros para o professor.
- [x] Expor detalhe de questão com habilidades associadas.
- [x] Permitir paginação e busca por texto, habilidade e status.
- [x] Criar testes para a visualização do Banco de Questões.

### 3.2 Montagem de prova por seleção
- [x] Separar a UI de criação da prova da UI de criação de questão.
- [x] Permitir adicionar/remover questões já existentes em uma prova.
- [x] Permitir ordenar questões e ajustar pesos antes da publicação.
- [x] Preservar Workflow B para provas sem Banco de Questões.
- [x] Criar testes para a montagem da prova por seleção de questões.

### 3.3 Visualização da prova
- [x] Exibir pré-visualização da prova montada.
- [x] Exibir resumo da composição da prova sem revelar gabarito.
- [x] Permitir revisão da prova antes da publicação.
- [x] Criar testes de confidencialidade para a pré-visualização.

### 3.4 Geração de OMR personalizado
- [x] Resolver os alunos elegíveis a partir das turmas vinculadas à prova.
- [x] Gerar uma folha personalizada por aluno.
- [x] Preencher nome, código do aluno e identificadores necessários.
- [x] Manter a compatibilidade com o fluxo OMR existente.
- [x] Criar testes de regressão para a geração individual e em lote.

### 3.5 Validação e regressão
- [x] Garantir que Workflow A e Workflow B continuem funcionando.
- [x] Garantir que tentativas online continuem imunes a vazamento de gabarito.
- [x] Garantir que a correção OMR continue usando `AnswerKeyItem.correct_answer`.
- [x] Garantir que turmas e matrículas sejam respeitadas na geração das folhas.

---

## 4. Dependências

- Banco de Questões funcional e reutilizável.
- `Exam`, `ExamQuestion`, `AnswerKey` e `AnswerKeyItem` já consolidados.
- Turmas e matrículas já existentes.
- Layout registry OMR e pipeline PDF já disponíveis.
- RBAC e isolamento de acesso já implementados.

---

## 5. Fora de Escopo Desta Etapa

- Anti-cheating analítico e dashboard docente de suspeição.
- Novo modelo de correção.
- Mudanças no motor de tentativas online.
- Processamento OMR em lote com escaneamento multipágina.
- Abstração de storage em nuvem para uploads OMR.
- Adaptador MinIO/S3 para uploads OMR, que pode ser introduzido depois da estabilização do MVP.

---

## 6. Definition of Done

Esta etapa foi considerada concluída porque:

1. o professor pode montar uma prova selecionando questões existentes;
2. o professor pode visualizar a prova antes de publicar;
3. a publicação continua gerando `AnswerKey` imutável;
4. folhas OMR personalizadas podem ser geradas por aluno;
5. o fluxo respeita turmas, matrículas e RBAC;
6. Workflow A, Workflow B, online e OMR continuam funcionando;
7. testes automatizados cobrem visualização, montagem, preview e geração personalizada;
8. a documentação do roadmap e do status reflete este novo passo.
