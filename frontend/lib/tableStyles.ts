import type { TableStyles } from 'react-data-table-component';

export const dataTableStyles: TableStyles = {
  table: {
    style: {
      backgroundColor: 'transparent',
    },
  },
  headRow: {
    style: {
      minHeight: '44px',
      backgroundColor: 'rgba(37, 99, 235, 0.08)',
      borderBottom: '1px solid var(--border)',
    },
  },
  headCells: {
    style: {
      fontSize: '12px',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.12em',
      color: 'var(--muted)',
      paddingTop: '12px',
      paddingBottom: '12px',
    },
  },
  rows: {
    style: {
      backgroundColor: 'rgba(255, 255, 255, 0.72)',
      color: 'var(--ink)',
      minHeight: '54px',
      borderBottom: '1px solid var(--border)',
    },
    highlightOnHoverStyle: {
      backgroundColor: 'rgba(37, 99, 235, 0.06)',
    },
  },
  pagination: {
    style: {
      borderTop: '1px solid var(--border)',
      color: 'var(--muted)',
      backgroundColor: 'transparent',
    },
  },
};

export const dataTablePaginationOptions = {
  rowsPerPageText: 'Rows',
  rangeSeparatorText: 'of',
};
