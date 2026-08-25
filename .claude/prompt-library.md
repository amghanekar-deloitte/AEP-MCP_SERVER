# Prompt Library

Quick-reference prompts for common engineering tasks. Copy, adjust to your context, and go.

---

## Planning & Analysis

**1. Plan a feature from a work item or requirement**
```text
/planner #12345
```

**2. Plan a feature from a specification**
```text
/planner build the account settings flow described in this specification: <spec-or-requirements-reference>
```

**3. Plan a feature with both requirements and reference material**
```text
/planner #12345 using this reference implementation: <repo-link-or-doc>
```

**4. Plan a backend service or API**
```text
/planner I need a service that fetches product data from an external API and caches responses for 10 minutes
```

**5. Analyze reuse before building**
```text
/planner check if we already have something that could be extended for a new export workflow with retries, status tracking, and notifications
```

---

## Backend

**6. Create a backend model, handler, or service**
```text
/build backend create the backend model for the hero feature that exposes title, description, image reference, and CTA link
```

**7. Create an API endpoint**
```text
/build backend create a GET endpoint for search results with pagination
```

**8. Create a scheduled job**
```text
/build backend create a scheduled job that runs nightly to clean up expired session tokens
```

**9. Debug a backend error**
```text
/debug NullPointerException in ProductService.getTitle() when the title field is missing
```

---

## Frontend

**10. Create a frontend feature**
```text
/build frontend create the UI for the account settings screen with validation, loading, and error states
```

**11. Extend an existing shared UI primitive**
```text
/build frontend extend the shared form field primitive to support inline help text and async validation
```

**12. Build a frontend feature from a reference specification**
```text
/planner build the onboarding flow from this specification: <spec-reference>
/build frontend implement the onboarding flow and match the interaction and validation requirements
```

**13. Fix an accessibility issue**
```text
/debug the carousel fails accessibility audit — missing labels on navigation buttons and focus is not managed when the slide changes
```

---

## Full-Stack & Data

**14. Build a full-stack feature**
```text
/build full-stack implement the login form, validation rules, and backend authentication flow
```

**15. Create a data model or schema**
```text
/build backend create a Product data model with name, description, price, sku, and category
```

**16. Fetch backend data in a frontend app**
```text
/build frontend create the client-side data layer for products and handle loading, error, and empty states
```

**17. Add an integration**
```text
/build backend integrate with Salesforce CRM to sync user profile data on form submission
```

---

## Testing & Review

**18. Generate test cases for a feature**
```text
/generate-test-cases checkout flow with validation, retries, error handling, and accessibility expectations
```

**19. Review current changes**
```text
/review-code
```

**20. Full review of a feature**
```text
/review-code review the checkout implementation for security, accessibility, performance, and code quality
```

**21. Validate a deployed implementation**
```text
/validate-implementation https://localhost:3000/checkout
```

---

## Debugging & Onboarding

**22. Explain how a module works**
```text
/debug-code ProductService.ts
```

**23. Debug a frontend rendering issue**
```text
/debug the checkout screen does not render correctly on mobile — the summary panel overflows below 768px
```

**24. Onboard to this project**
```text
/initialize-setup
/debug-code where is the search functionality implemented
```
