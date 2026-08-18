export interface DestructiveDialogCopy {
  title: string;
  message: string;
  warning: string;
  confirmLabel: string;
}

export function buildArchiveCopy(entityLabel: string, entityName: string): DestructiveDialogCopy {
  return {
    title: `Arquivar ${entityLabel}?`,
    message: `Arquivar ${entityLabel} ${entityName}?`,
    warning:
      'O item deixa de aparecer como ativo, mas o histórico e os vínculos já registrados permanecem preservados.',
    confirmLabel: 'Confirmar arquivamento',
  };
}

export function buildDeactivateCopy(entityLabel: string, entityName: string): DestructiveDialogCopy {
  return {
    title: `Inativar ${entityLabel}?`,
    message: `Inativar ${entityLabel} ${entityName}?`,
    warning:
      'A inativação preserva o histórico pedagógico e evita a perda de registros já associados.',
    confirmLabel: 'Confirmar inativação',
  };
}

export function buildDeleteCopy(entityLabel: string, entityName: string): DestructiveDialogCopy {
  return {
    title: `Excluir ${entityLabel}?`,
    message: `Excluir definitivamente ${entityLabel} ${entityName}?`,
    warning:
      'A exclusão é permanente. O histórico relacionado será preservado apenas quando o fluxo do sistema permitir a retenção.',
    confirmLabel: 'Confirmar exclusão',
  };
}
