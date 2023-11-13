import { useEffect, useState } from "react";
import { XObject } from "./xobject"
import { convert } from "./convert";
import { network } from "./socket";

export function XReactComponent({ xobject }: { xobject: XObject }) {
    const [render, setRender] = useState<any>(null);
    useEffect(() => {
        xobject.render().then(async (render) => {
            setRender(await convert(render));
        });
    }, [xobject]);
    useEffect(() => {
        network.socket.on('render', async ({id, data}: {id: number, data: any}) => {
            if (id === xobject.id) {
                setRender(await convert(data));
            }
        });
    }, [xobject]);
    return <>{render}</>;
}
