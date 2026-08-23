/**
 * Cliente HTTP Fetch com tratamento seguro de CSRF, Cookies HttpOnly e Erros.
 */

class ApiClient {
  constructor() {
    this.baseUrl = window.CONFIG?.API_BASE_URL || '/api';
  }

  /**
   * Obtém o token CSRF gravado no cookie pelo Django.
   */
  getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * Executa requisição HTTP Fetch segura.
   */
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    
    const headers = {
      'Accept': 'application/json',
      ...options.headers
    };

    // Adiciona Content-Type caso haja payload JSON
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    // Injeta cabeçalho CSRF em métodos de mutação
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrfToken = this.getCsrfToken();
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
    }

    const fetchConfig = {
      method,
      headers,
      credentials: 'include', // Envia Cookies de Sessão HttpOnly e CSRF em dev (portas diferentes) e prod
      ...options
    };

    try {
      const response = await fetch(url, fetchConfig);

      // Tratamento de Sessão Expirada / Hard Lock (401)
      if (response.status === 401) {
        console.warn('[ApiClient] Sessão expirada ou não autenticada (401).');
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      }

      // Tratamento de Acesso Proibido (403 RBAC)
      if (response.status === 403) {
        console.warn('[ApiClient] Acesso proibido por permissão RBAC (403).');
        window.dispatchEvent(new CustomEvent('auth:forbidden'));
      }

      // Tratamento de Throttling (429)
      if (response.status === 429) {
        console.warn('[ApiClient] Limite de requisições atingido (429).');
        window.dispatchEvent(new CustomEvent('api:throttled'));
      }

      // Tratamento de respostas sem corpo (ex: 204 No Content)
      if (response.status === 204) {
        return { success: true };
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        return Promise.reject({
          status: response.status,
          message: data.message || 'Erro na requisição.',
          details: data.details || data
        });
      }

      return data;
    } catch (error) {
      console.error(`[ApiClient Error] ${method} ${url}:`, error);
      throw error;
    }
  }

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body)
    });
  }

  put(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body)
    });
  }

  patch(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body)
    });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * Faz o download seguro de arquivos (PDF, CSV, OFX, XML) retornados pela API via Blob.
   * @param {string} endpoint 
   * @param {string} defaultFilename 
   */
  async downloadFile(endpoint, defaultFilename = 'download') {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const csrfToken = this.getCsrfToken();
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
        },
        credentials: 'include'
      });

      if (response.status === 401) {
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        throw new Error('Sessão expirada.');
      }

      if (response.status === 403) {
        window.dispatchEvent(new CustomEvent('auth:forbidden'));
        throw new Error('Acesso proibido.');
      }

      if (response.status === 429) {
        window.dispatchEvent(new CustomEvent('api:throttled'));
        throw new Error('Limite de requisições atingido. Aguarde um minuto.');
      }

      if (!response.ok) {
        const erroJson = await response.json().catch(() => ({}));
        throw new Error(erroJson.message || erroJson.detail || 'Falha ao baixar arquivo.');
      }

      // Obtém o nome do arquivo pelo cabeçalho Content-Disposition se existir
      let filename = defaultFilename;
      const disposition = response.headers.get('Content-Disposition');
      if (disposition && disposition.indexOf('filename=') !== -1) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);

      return { success: true, filename };
    } catch (error) {
      console.error('[ApiClient Download Error]:', error);
      throw error;
    }
  }
}

window.api = new ApiClient();

