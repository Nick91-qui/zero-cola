# COLA-ZERO

Plataforma de avaliação online com banco de questões reutilizável, tentativas dinâmicas e monitoramento transparente de integridade.

---

# 1. Visão geral

O COLA-ZERO é uma plataforma educacional orientada por:

- banco de questões reutilizável
- provas compostas por questões reutilizadas
- execução de tentativa com uma questão por vez
- correção automática e manual
- auditoria de ações sensíveis
- conformidade com LGPD

Modelo central do sistema:

> Question Bank + Attempt Engine

A prova é uma configuração de entrega. A entidade principal do domínio é a questão.

---

# 2. Arquitetura

- Frontend: Next.js
- Backend: FastAPI
- Banco de dados: PostgreSQL
- Infraestrutura: Docker e Docker Compose

Princípios principais:

- simplicidade
- segurança primeiro
- privacidade por padrão
- separação entre interface, regras de negócio e persistência

---

# 3. Funcionalidades do MVP

## Alunos

- autenticação
- acesso às provas atribuídas
- início de tentativas
- resposta de uma questão por vez
- visualização de resultados liberados

## Professores

- criação e gestão de questões
- criação e publicação de provas
- correção de respostas quando aplicável
- acesso a relatórios básicos de monitoramento

## Administradores

- gestão de usuários
- acesso a configurações da plataforma
- acesso a logs de auditoria

---

# 4. Fluxo da prova

1. aluno autentica
2. aluno inicia tentativa
3. frontend solicita a próxima questão
4. backend entrega apenas a questão atual
5. aluno envia resposta
6. backend persiste imediatamente
7. frontend solicita a próxima questão
8. tentativa é finalizada e corrigida conforme o tipo da questão

Regra central:

O frontend nunca deve receber a prova inteira de uma vez.

---

# 5. Segurança

## 5.1 Autenticação

- JWT access token
- JWT refresh token
- hash de senha com Argon2 preferencialmente
- bcrypt como alternativa aceitável

---

## 5.2 Autorização

- RBAC obrigatório
- perfis:
  - student
  - teacher
  - admin
- todo endpoint deve validar permissões

---

## 5.3 Auditoria

Ações sensíveis devem gerar logs, incluindo:

- login
- troca de senha
- criação de prova
- publicação de prova
- alteração de nota

---

# 6. Monitoramento

O sistema registra eventos relacionados à tentativa, como:

- visibilitychange
- blur
- focus
- fullscreen enter
- fullscreen exit

Esses eventos são usados para análise posterior e geração de relatórios.

COLA-ZERO não é um lockdown browser.

O sistema não deve afirmar que consegue:

- detectar uso de ChatGPT
- detectar outro dispositivo
- detectar telefones externos
- detectar capturas de tela de forma confiável
- impedir toda forma de cola

---

# 7. LGPD

O sistema segue princípios de:

- minimização de dados
- finalidade explícita
- transparência
- segurança
- retenção compatível com exigências legais e acadêmicas

Dados tratados no MVP:

- identificação de conta
- respostas de prova
- eventos relacionados à tentativa
- logs de auditoria

Capacidades necessárias:

- aviso de monitoramento
- exportação de dados do usuário
- anonimização quando legalmente permitida

---

# 8. Estrutura do projeto

```text
cola-zero/
├── backend/
├── frontend/
├── infra/
├── .env.example
└── README.md
```

---

# 9. Estado do MVP

O MVP é considerado concluído quando:

- usuários autenticam com segurança
- professores criam questões
- professores criam e publicam provas
- alunos realizam tentativas
- respostas são persistidas e corrigidas
- eventos de monitoramento são registrados
- relatórios básicos são gerados
- requisitos essenciais de LGPD são atendidos

---

# 10. Execução

Os detalhes de execução devem ser definidos nos módulos de backend, frontend e infraestrutura conforme o repositório evoluir.