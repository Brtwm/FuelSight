type RequestWithRefreshParams = {
  input: RequestInfo | URL;
  init?: RequestInit;
  accessToken: string | null;
  doFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
  refreshAccessToken: () => Promise<string | null>;
};

function withAuthHeaders(init: RequestInit | undefined, accessToken: string | null): RequestInit {
  const headers = new Headers(init?.headers);
  if (accessToken) {
    headers.set('authorization', `Bearer ${accessToken}`);
  } else {
    headers.delete('authorization');
  }

  return {
    ...init,
    headers,
    credentials: init?.credentials ?? 'include',
  };
}

export async function requestWithRefresh({
  input,
  init,
  accessToken,
  doFetch,
  refreshAccessToken,
}: RequestWithRefreshParams): Promise<Response> {
  const initialResponse = await doFetch(input, withAuthHeaders(init, accessToken));
  if (initialResponse.status !== 401) {
    return initialResponse;
  }

  const nextToken = await refreshAccessToken();
  if (!nextToken) {
    return initialResponse;
  }

  return doFetch(input, withAuthHeaders(init, nextToken));
}
