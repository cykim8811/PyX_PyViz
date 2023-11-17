
import { useEffect, useState } from "react"
import { network } from "./socket"
import { XReactComponent } from "./XReactComponent";
import { XObject } from "./xobject";

export default function App() {
	const [root, setRoot] = useState<any>(null);
	useEffect(() => {
		const queryParams = new URLSearchParams(window.location.search);
		const roomname = queryParams.get('room');
		network.requestConst('root', roomname).then((rootId) => {
			if (rootId === null) return;
			setRoot(<XReactComponent xobject={new XObject(rootId, network)} />);
		});
	}, []);
	if (root === null) {
		return <div>Loading...</div>
	}
	return root;
}
