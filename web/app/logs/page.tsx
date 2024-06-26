"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { useRouter } from "next/navigation";
import { Audio } from "react-loader-spinner";
import axios from "axios";
import "react-toastify/dist/ReactToastify.css";

interface log {
    index: number;
    duration: number;
    service: string;
    protocol_type: string;
    src_bytes: number;
    dst_bytes: number;
    count: number;
    srv_count: number;
}

const attacks = ["Dos", "Probe", "R2L", "U2R", "normal"];

const COLUMNS: GridColDef[] = [
    //     {
    //   field: 'index',
    //   headerName: 'Index',
    //   width: 70,
    //   valueGetter: (params) => params.row.index + 1
    // },
    { field: "timestamp", headerName: "Timestamp", width: 220 },
    { field: "switchid", headerName: "Switch ID", width: 150 },
    { field: "source", headerName: "Source IP", width: 150 },
    { field: "destination", headerName: "Destination IP", width: 150 },
    { field: "size", headerName: "Packet Size", width: 150 },
    { field: "in_port", headerName: "Input Port", width: 150 },
];

const rows = [
    { id: 1, lastName: "Snow", firstName: "Jon", age: 35 },
    { id: 2, lastName: "Lannister", firstName: "Cersei", age: 42 },
    { id: 3, lastName: "Lannister", firstName: "Jaime", age: 45 },
    { id: 4, lastName: "Stark", firstName: "Arya", age: 16 },
    { id: 5, lastName: "Targaryen", firstName: "Daenerys", age: null },
    { id: 6, lastName: "Melisandre", firstName: null, age: 150 },
    { id: 7, lastName: "Clifford", firstName: "Ferrara", age: 44 },
    { id: 8, lastName: "Frances", firstName: "Rossini", age: 36 },
    { id: 9, lastName: "Roxie", firstName: "Harvey", age: 65 },
];

export default function Home() {
    const [logs, setLogs] = useState<log[]>([]);
    const [loaded, setLoaded] = useState(false);
    const router = useRouter();

    const fetchLogs = async () => {
        const result = await axios.get("http://localhost:8000/fetch");
        const data = result.data;
        // @ts-ignore
        setLogs(data.map((row, index: number) => ({ ...row, index })));
        console.log(result);
    };

    useEffect(() => {
        if (localStorage.getItem("password") != "vaibhav") {
            router.push("/");
        }
        const socket = new WebSocket("ws://localhost:8765");

        socket.onopen = () => {
            console.log("WebSocket connected!");
        };

        socket.onmessage = (event) => {
            const result = JSON.parse(event.data);
            if (result.type == "log") {
                console.log(result.data);
                setLogs((prevLogs) => [...prevLogs, result.data]);
            }
        };

        setLoaded(true);

        return () => {
            socket.close();
        };
    }, []);

    if (!loaded)
        return (
            <div
                style={{
                    width: "98vw",
                    height: "80vh",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                <Audio
                    height="200"
                    width="200"
                    radius="20"
                    color="green"
                    ariaLabel="three-dots-loading"
                    // @ts-ignore
                    wrapperStyle
                    // @ts-ignore
                    wrapperClass
                />
            </div>
        );
    return (
        <main>
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <h1 className="px-4 py-2 bg-blue-600 text-white m-2">
                    Live Controller Logs
                </h1>
                <div style={{ height: "80vh" }}>
                    <DataGrid
                        style={{ minHeight: 400 }}
                        rows={logs}
                        columns={COLUMNS}
                        getRowId={(row) => row.timestamp}
                        initialState={{
                            pagination: {
                                paginationModel: { page: 0, pageSize: 10 },
                            },
                        }}
                        // pageSizeOptions={[5, 10]}
                        autoPageSize
                    />
                </div>
            </div>
        </main>
    );
}
