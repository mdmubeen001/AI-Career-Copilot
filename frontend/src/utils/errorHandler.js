/**
 * Formats API errors returned from Django REST Framework into readable strings.
 */
export function formatApiError(error) {
  if (!error) return 'An unexpected error occurred.';

  // Network or setup errors
  if (!error.response) {
    if (error.request) {
      return 'Unable to connect to the server. Please check your internet connection or backend status.';
    }
    return error.message || 'An unexpected error occurred.';
  }

  const { data, status } = error.response;

  if (status === 401) {
    if (data?.detail) return data.detail;
    return 'Invalid credentials or session expired. Please log in again.';
  }

  if (status === 403) {
    return data?.detail || 'You do not have permission to perform this action.';
  }

  if (status === 404) {
    return data?.detail || 'The requested resource was not found.';
  }

  // Handle DRF validation error structures
  if (data && typeof data === 'object') {
    if (data.detail) return data.detail;
    if (data.message) return data.message;

    const messages = [];
    for (const [key, value] of Object.entries(data)) {
      const fieldName = key === 'non_field_errors' ? '' : `${key}: `;
      if (Array.isArray(value)) {
        messages.push(`${fieldName}${value.join(' ')}`);
      } else if (typeof value === 'string') {
        messages.push(`${fieldName}${value}`);
      } else if (typeof value === 'object') {
        messages.push(`${fieldName}${JSON.stringify(value)}`);
      }
    }

    if (messages.length > 0) {
      return messages.join(' | ');
    }
  }

  return `Request failed with status ${status}.`;
}
