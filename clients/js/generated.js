// Generated from the public contract; do not edit.
// Public spec SHA256: efad44769877e7403dfc7981b22e27b8bf6e0bc4f57fd988b8653c892b7705ce
export const API_BASE_URL = "https://luxdb.net/api/v1";
export const ERROR_CODES = [
  "unauthorized",
  "plan",
  "payment_required",
  "rate_limited",
  "search_cap",
  "account_paused",
  "account_closed",
  "member_limit_reached",
  "not_found",
  "method_not_allowed",
  "bad_request",
  "api_disabled",
  "maintenance",
  "internal_error"
];
export const ERROR_MODES = [
  "maintenance",
  "stopped"
];
export const OPERATIONS = {
  "article": {
    "path": "/article",
    "authenticated": true,
    "parameters": [
      {
        "name": "codes",
        "in": "query",
        "required": true,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "search": {
    "path": "/search",
    "authenticated": true,
    "parameters": [
      {
        "name": "q",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "department",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "category",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "type",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "color",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "status",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "page",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "changes": {
    "path": "/changes",
    "authenticated": true,
    "parameters": [
      {
        "name": "since",
        "in": "query",
        "required": true,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "page",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "family": {
    "path": "/family/{id}",
    "authenticated": true,
    "parameters": [
      {
        "name": "id",
        "in": "path",
        "required": true,
        "schema": {
          "type": "string",
          "pattern": "^nvprod\\d+v$"
        }
      },
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "resolve": {
    "path": "/resolve",
    "authenticated": true,
    "parameters": [
      {
        "name": "url",
        "in": "query",
        "required": true,
        "schema": {
          "type": "string"
        }
      },
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "index": {
    "path": "/index",
    "authenticated": true,
    "parameters": [
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "snapshot": {
    "path": "/snapshot",
    "authenticated": true,
    "parameters": [
      {
        "name": "brand",
        "in": "query",
        "required": false,
        "schema": {
          "type": "string"
        }
      }
    ]
  },
  "openapi": {
    "path": "/openapi",
    "authenticated": false,
    "parameters": []
  }
};
