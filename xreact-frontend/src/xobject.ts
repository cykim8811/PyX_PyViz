
import { Network } from "./socket";

export class XObject {
    id: number;
    network: Network;
    constructor(id: number, network: Network) {
        this.id = id;
        this.network = network;
    }
    async render() {
        return await this.network.request('render', this.id);
    }
}
