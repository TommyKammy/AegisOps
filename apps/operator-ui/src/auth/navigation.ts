export interface Redirector {
  replace: (href: string) => void;
}

export const windowLocationRedirector: Redirector = {
  replace(href) {
    window.location.assign(href);
  },
};
