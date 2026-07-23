const SAFE_ERROR_MESSAGE = 'Could not archive articles. Please try again.';

export const runBulkArchive = async ({
  daysOld,
  apiUrl,
  authHeaders,
  confirmAction,
  fetchImpl,
  onConfirmed,
}) => {
  const confirmed = confirmAction(
    `Archive articles older than ${daysOld} days? They will remain available in the archive.`
  );

  if (!confirmed) {
    return { status: 'cancelled' };
  }

  if (onConfirmed) {
    onConfirmed();
  }

  try {
    const response = await fetchImpl(
      `${apiUrl}/api/admin/articles/bulk-archive`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify({ days_old: daysOld }),
      }
    );

    let data;
    try {
      data = await response.json();
    } catch {
      return { status: 'error', message: SAFE_ERROR_MESSAGE };
    }

    if (!response.ok || data?.success !== true) {
      return { status: 'error', message: SAFE_ERROR_MESSAGE };
    }

    const archivedCount = data.archived_count;
    if (
      typeof archivedCount !== 'number'
      || !Number.isInteger(archivedCount)
      || archivedCount < 0
    ) {
      return { status: 'error', message: SAFE_ERROR_MESSAGE };
    }

    return {
      status: 'success',
      archivedCount,
      message: `Archived ${archivedCount} article${archivedCount === 1 ? '' : 's'} older than ${daysOld} days.`,
    };
  } catch {
    return { status: 'error', message: SAFE_ERROR_MESSAGE };
  }
};
