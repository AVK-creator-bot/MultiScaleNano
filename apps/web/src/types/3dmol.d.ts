declare module "3dmol" {
  interface ViewerSpec {
    backgroundColor?: string;
  }

  interface ViewerStyle {
    sphere?: { radius?: number; color?: string; opacity?: number };
  }

  interface Viewer {
    addModel(data: string, format: string): unknown;
    setStyle(selection: Record<string, string>, style: ViewerStyle): void;
    zoomTo(): void;
    render(): void;
    clear(): void;
  }

  function createViewer(element: HTMLElement, spec?: ViewerSpec): Viewer;

  export type { Viewer, ViewerSpec, ViewerStyle };

  export default { createViewer };
}
