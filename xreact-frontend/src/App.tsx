
import { useEffect, useState } from "react"
import { network } from "./socket"
import { XReactComponent } from "./XReactComponent";
import { XObject } from "./xobject";

export default function App() {
	const [root, setRoot] = useState<any>(null);
	useEffect(() => {
		network.requestConst('root').then((rootId) => {
			if (rootId === null) return;
			setRoot(<XReactComponent xobject={new XObject(rootId, network)} />);
		});
	}, []);
	if (root === null) {
		return <div>Loading...</div>
	}
	return root;
}
