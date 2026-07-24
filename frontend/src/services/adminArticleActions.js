const SAFE_ARCHIVE_ERROR = 'Could not archive the selected articles. Please try again.';

const isValidCount = (value) => (
  typeof value === 'number' && Number.isInteger(value) && value >= 0
);

const safeCount = (value) => (isValidCount(value) ? value : 0);

export const archiveSelectedArticles = async ({
  selectedIds,
  apiUrl,
  authHeaders,
  confirmAction,
  fetchImpl,
  onConfirmed,
}) => {
  const articleIds = Array.from(selectedIds);
  const confirmed = await confirmAction({
    title: `Archive ${articleIds.length} Selected Articles`,
    description: `Archive ${articleIds.length} selected article(s)? They will remain available in the archive.`,
    variant: 'warning',
    confirmText: 'Archive Selected',
    cancelText: 'Cancel',
  });

  if (!confirmed) {
    return { status: 'cancelled' };
  }

  if (onConfirmed) {
    onConfirmed();
  }

  const archivedIds = [];
  const failedIds = [];

  for (const articleId of articleIds) {
    try {
      const response = await fetchImpl(
        `${apiUrl}/api/admin/articles/${encodeURIComponent(articleId)}/archive`,
        {
          method: 'POST',
          headers: authHeaders,
        }
      );

      if (response.ok) {
        archivedIds.push(articleId);
      } else {
        failedIds.push(articleId);
      }
    } catch {
      failedIds.push(articleId);
    }
  }

  if (archivedIds.length === 0) {
    return {
      status: 'error',
      archivedIds,
      failedIds,
      message: SAFE_ARCHIVE_ERROR,
    };
  }

  if (failedIds.length > 0) {
    return {
      status: 'partial',
      archivedIds,
      failedIds,
      message: `Archived ${archivedIds.length} articles. ${failedIds.length} could not be archived.`,
    };
  }

  return {
    status: 'success',
    archivedIds,
    failedIds,
    message: `Archived ${archivedIds.length} selected articles.`,
  };
};

export const removeArchivedSelection = (selectedIds, archivedIds) => {
  const archived = new Set(archivedIds);
  return new Set(
    Array.from(selectedIds).filter(articleId => !archived.has(articleId))
  );
};

export const formatImportCompletion = (result = {}) => {
  const publicImported = safeCount(result.public_imported);
  const manualReviewImported = safeCount(result.manual_review_imported);
  const totalImported = safeCount(result.total_imported);
  const hasDetailedCounts = (
    isValidCount(result.public_imported)
    || isValidCount(result.manual_review_imported)
  );
  const retained = hasDetailedCounts
    ? publicImported + manualReviewImported
    : totalImported;
  const estimatedCost = (
    typeof result.estimated_cost_usd === 'number'
    && Number.isFinite(result.estimated_cost_usd)
    && result.estimated_cost_usd >= 0
  )
    ? result.estimated_cost_usd
    : null;

  let message;
  if (publicImported === 0 && manualReviewImported === 0 && retained === 0) {
    message = 'Import completed: no new articles were retained. Existing duplicates, source filters, image requirements or quality checks may have excluded the available candidates.';
  } else if (publicImported === 0 && manualReviewImported > 0) {
    message = `Import completed: no public articles were added; ${manualReviewImported} articles were sent to Manual Review.`;
  } else {
    message = `Import completed: ${publicImported} public articles added, ${manualReviewImported} sent to Manual Review, ${retained} total retained.`;
  }

  return {
    publicImported,
    manualReviewImported,
    retained,
    estimatedCost,
    message,
  };
};
