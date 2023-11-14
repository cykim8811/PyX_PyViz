
import { useEffect, useState } from "react";


export function Xinput(props: any): JSX.Element {
    const [value, setValue] = useState(props.value);
    
    const serverValue = props.value;
    const serverOnChange = props.onChange || (() => {});

    const [onChangeTimeout, setOnChangeTimeout] = useState<any>(null);

    const onChange = (e: any) => {
        setValue(e.target.value);
        const newTimeout = setTimeout(() => {
            serverOnChange(e);
        }, 0);
        if (onChangeTimeout !== null) {
            clearTimeout(onChangeTimeout);
        }
        setOnChangeTimeout(newTimeout);
    };

    useEffect(() => {
        if (serverValue === value) return;
        console.log("Discrepancy - serverValue: " + serverValue + " value: " + value)
        setValue(serverValue);
    }, [serverValue]);

    const inputProps = {
        ...props,
        value,
        onChange,
    };
    return <input {...inputProps} />;
}
