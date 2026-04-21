import { BrowserRouter } from "react-router-dom";
import {
  OperatorAppDependencies,
  OperatorRoutes,
  createDefaultDependencies,
} from "./app/OperatorRoutes";

export function OperatorApp({
  dependencies,
}: {
  dependencies?: Partial<OperatorAppDependencies>;
}) {
  const resolved = createDefaultDependencies(dependencies);

  return (
    <BrowserRouter>
      <OperatorRoutes dependencies={resolved} />
    </BrowserRouter>
  );
}

export default function App() {
  return <OperatorApp />;
}
