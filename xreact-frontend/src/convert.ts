
import { XReactComponent } from "./XReactComponent";
import { createElement } from "react";
import { XObject } from "./xobject";
import { network } from "./socket";
import { Xinput } from "./xcomponents/xinput";

// Converts any object to serializable object
// If object is not serializable, it will be discarded
function serializable(arg: any, depth: number=3): any {
	if (depth === 0) return undefined;
	if (typeof arg === 'function') { // discard
		return undefined;
	} else if (typeof arg === 'object') {
		if (Array.isArray(arg)) {
			return arg.map((item) => serializable(item, depth-1));
		} else if (arg === null) {
			return null;
		} else {
			const obj: any = {};
			for (const key in arg) {
				const value = serializable(arg[key], depth-1);
				if (value !== undefined) {
					obj[key] = value;
				}
			}
			return obj;
		}
	} else {
		return arg;
	}
}

/*
 * Converts xelement to JSX.Element
 * xelement: {
 *   tag: string, // string: HTML tag
 *   props: {[key: string]: any}
 *   children: xelement[]
 * }
 */

export async function convert(xelement: any): Promise<JSX.Element|string> {
	if (typeof xelement === 'string') return xelement;
	if (xelement.children === undefined) xelement.children = [];
    if (xelement.props === undefined) xelement.props = {};
    for (const key in xelement.props) {
        if (xelement.props[key].__call__ !== undefined) {
            const ftnId = xelement.props[key].__call__;
            xelement.props[key] = (...args: any[]) => {
                args = args.map((arg) => serializable(arg, 3));
                network.socket.emit('call', ftnId, ...args);
            }
        }
    }
	const children = await Promise.all(xelement.children.map((child: any) => {
		if (typeof child === 'number') {
			return createElement(XReactComponent, {xobject: new XObject(child, network), key: child});
		} else {
			return convert(child);
		}
	}));
	if (xelement.tag === 'input') {
		xelement.tag = Xinput;
	}
	return createElement(
		xelement.tag,
		xelement.props,
		...children
	);
}
