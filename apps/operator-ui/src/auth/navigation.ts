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

export const windowLocationRedirector: Redirector = {
  replace(href) {
    if (
      typeof window === "undefined" ||
      !window.location ||
      typeof window.location.replace !== "function"
    ) {
      throw new Error("Window location is unavailable for auth redirects.");
    }

    window.location.replace(href);
  },
};
