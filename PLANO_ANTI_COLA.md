# COLA-ZERO — Planejamento de Integridade Online & Privacidade (`PLANO_ANTI_COLA.md`)

> **Single Source of Truth** para a estratégia de monitoramento de integridade em exames online, eventos de segurança suportados, auditoria de ações sensíveis, política de privacidade e conformidade LGPD.

---

## 1. Filosofia de Integridade e Limites Técnicos

> [!IMPORTANT]
> **COLA-ZERO NÃO É UMA PLATAFORMA DE VIGILÂNCIA**.
> 
> O monitoramento existe exclusivamente para registrar evidências de eventos observáveis do navegador durante exames online, promovendo integridade com total transparência.
> 
> **OMR NÃO FAZ PARTE DE MECANISMOS ANTI-COLA**. O OMR é unicamente um sistema de leitura e correção física de cartões-resposta impressos.

### Afirmações NÃO Suportadas (Proibições Técnicas)
O COLA-ZERO **NUNCA DEVE prometer ou alegar**:
- Detecção de uso de ChatGPT ou inteligências artificiais externas.
- Detecção de segundos monitores ou dispositivos externos (ex: celulares).
- Bloqueio ou detecção infalível de capturas de tela (screenshots).
- Prevenção total contra todas as formas de fraude.

Tais promessas são tecnicamente imprecisas em ambiente web padrão e não fazem parte do escopo da plataforma.

---

## 2. Eventos de Segurança Suportados (`security_events`)

Durante a realização de uma prova online, a aplicação pode registrar eventos observáveis do navegador e persistir os registros na tabela `security_events`. A infraestrutura backend para receber, armazenar e consultar esses eventos já existe; a análise de suspeitas continua como funcionalidade futura.

### Lista de Eventos Observáveis
1. `visibilitychange`: Registra quando a aba do exame perde a visibilidade (ex: aluno mudou de aba).
2. `blur`: Registra quando a janela do navegador perde o foco.
3. `focus`: Registra quando a janela do navegador ganha o foco novamente.
4. `fullscreen_enter`: Registra quando o aluno entra em modo de tela cheia.
5. `fullscreen_exit`: Registra quando o aluno sai do modo de tela cheia.

### Modelo de Dados de Eventos de Segurança
```sql
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'visibilitychange', 'blur', 'focus', 'fullscreen_enter', 'fullscreen_exit'
    metadata JSONB NULL, -- Timestamps e detalhes contextuais
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 3. Transparência e Consentimento Explícito

Em estrita observância à LGPD (Lei Geral de Proteção de Dados):
1. **Aviso Prévisível**: antes de iniciar qualquer tentativa online, o aluno visualiza um aviso claro informando quais eventos de tela poderão ser registrados durante a prova.
2. **Registro de Consentimento**: o consentimento do aluno é gravado via API (`POST /consents/monitoring`) antes do início da coleta de eventos.
3. **Indicador Visível**: durante a prova, a interface pode exibir um indicador discreto de monitoramento transparente.

---

## 4. Auditoria de Ações Sensíveis (`audit_logs`)

Além do monitoramento de tela durante provas online, o sistema mantém uma trilha de auditoria imutável para ações administrativas e pedagógicas sensíveis na tabela `audit_logs`.

### Eventos Auditáveis
- Autenticação de usuários (sucesso e falha de login).
- Alteração de senha ou perfil de usuário.
- Criação, edição ou publicação de exames.
- Alteração manual de notas ou edição de leituras OMR pelo professor.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 5. Diretrizes de Privacidade e LGPD

### 5.1 Minimização de Dados (Minimum Data Collection)
O COLA-ZERO coleta estritamente o mínimo de dados necessários para a prestação do serviço educacional:
- **Dados Coletados**: dados de conta (`email`, `role`, `student_code`), respostas de exames, eventos de segurança da tentativa, logs de auditoria e consentimentos.
- **Dados Estritamente Proibidos de Coleta**: arquivos pessoais do dispositivo, fotos da câmera/webcam sem consentimento explícito, histórico de navegação global fora do aplicativo, contatos ou dados de outros aplicativos do sistema operacional.

### 5.2 Direitos do Titular de Dados
- **Exportação de Dados**: Endpoint `GET /api/v1/me/data-export` gera um pacote estruturado em JSON com todos os dados pessoais e acadêmicos do usuário.
- **Solicitação de Anonimização**: Endpoint `POST /api/v1/me/request-anonymization` registra a solicitação de anonimização, respeitando prazos de retenção de registros acadêmicos legais.
- **Política de Privacidade**: Endpoint e página pública `GET /api/v1/privacy-policy` detalhando a política de dados.

### 5.3 Estado Atual

- A infraestrutura de `consents`, `audit_logs`, `security_events`, exportação de dados e anonimização suave já está implementada no backend.
- A análise anti-cheating detalhada, a correlação de eventos e o painel docente de revisão permanecem como evolução futura.
