# Checklist de Pontas Soltas

> Lista priorizada dos ajustes feitos para fechar o fluxo de cadastro e reduzir superfície pública.

## P0

- [x] Remover o cadastro público em `/auth/register` do backend.
- [x] Migrar o frontend para autenticação baseada em cookie HttpOnly.
- [x] Eliminar o método `register()` do contexto de auth do frontend.
- [x] Garantir que o acesso à criação de usuários fique restrito a `/admin/users`.

## P1

- [x] Atualizar os testes que dependiam de `/auth/register` para criação direta em banco.
- [x] Verificar que `auth/me` funciona com sessão por cookie.
- [x] Corrigir a documentação de status e auditoria para refletir o novo fluxo.

## P2

- [ ] Revisar referências históricas em arquivos de arquivo morto (`docs/archive/`) se for desejado um alinhamento total do histórico.
