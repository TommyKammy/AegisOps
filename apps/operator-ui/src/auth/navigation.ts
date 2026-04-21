export interface Redirector {
  replace: (href: string) => void;
}

export function createWindowLocationRedirector(
  location: Pick<Location, "replace">,
): Redirector {
  return {
    replace(href) {
      location.replace(href);
    },
  };
}

export const windowLocationRedirector = createWindowLocationRedirector(
  window.location,
);
