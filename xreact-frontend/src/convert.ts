
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
			const preventDefault = xelement.props[key].preventDefault;
			const stopPropagation = xelement.props[key].stopPropagation;
			const returnFormat = xelement.props[key].returnFormat;
            const ftnId = xelement.props[key].__call__;
            xelement.props[key] = (...args: any[]) => {
				if (preventDefault) {
					args[0].preventDefault();
				}
				if (stopPropagation) {
					args[0].stopPropagation();
				}
				if (returnFormat !== undefined && Array.isArray(returnFormat)) {
					// returnFormat: A format of return value
					// ex) [{'clientX': true, 'clientY': true}, ...]
					// If returnFormat is undefined, use serializable with depth 2
					// getReturnFormat: Filter return value with returnFormat
					// ex) returnFormat: [{'clientX': true, 'clientY': true, 'target': {'id': true}}]
					// obj: {'clientX': 10, 'clientY': 20, 'target': {'id': 'abc', 'className': 'def'}}
					// return: {'clientX': 10, 'clientY': 20, 'target': {'id': 'abc'}}
					function getReturnFormat(obj: any, format: any): any {
						const ret: any = {};
						for (const key in format) {
							if (typeof format[key] === 'boolean') {
								if (format[key]) {
									ret[key] = obj[key];
								}
							} else if (typeof format[key] === 'object') {
								ret[key] = getReturnFormat(obj[key], format[key]);
							}
						}
						return ret;
					}
					args = args.map((arg, i) => getReturnFormat(arg, returnFormat[i]));
				} else {
                args = args.map((arg) => serializable(arg, 2));
				}
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
