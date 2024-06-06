"use client";
import { useEffect, useState } from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { useRouter } from "next/navigation";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
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
    {
        field: "index",
        headerName: "Index",
        width: 70,
        valueGetter: (params) => params.row.index + 1,
    },
    { field: "timestamp", headerName: "Timestamp", width: 220 },
    { field: "duration", headerName: "Duration", width: 100 },
    { field: "service", headerName: "Service", width: 100 },
    { field: "protocol_type", headerName: "Protocol Type", width: 120 },
    { field: "src_bytes", headerName: "Source Bytes", width: 150 },
    { field: "dst_bytes", headerName: "Destination Bytes", width: 150 },
    { field: "count", headerName: "Count", width: 100 },
    { field: "srv_count", headerName: "Service Count", width: 120 },
    {
        field: "attack",
        headerName: "Attack",
        width: 100,
        valueGetter: (params) => attacks[params.row.attack],
    },
];

export default function Home() {
    const [logs, setLogs] = useState<log[]>([]);
    const router = useRouter();

    const fetchLogs = async () => {
        const result = await axios.get("http://localhost:8000/fetch");
        const data = result.data;
        // @ts-ignore
        setLogs(data.map((row, index: number) => ({ ...row, index })));
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
            let result = JSON.parse(event.data);
            if (result && result.type === "alert") {
                console.log(result.data);
                toast.error("Attack has occured!");
                setLogs((prevLogs) => {
                    return [...prevLogs, ...result.data].map(
                        (value, index) => ({ ...value, index: index })
                    );
                });
            }
        };

        // fetchLogs();

        return () => {
            socket.close();
        };
    }, []);

    return (
        <main>
            <ToastContainer />
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <h1 className="px-4 py-2 bg-red-600 text-white m-2">
                    Live Alerts
                </h1>
                <div style={{ height: "80vh" }}>
                    <DataGrid
                        rows={logs}
                        columns={COLUMNS}
                        getRowId={(row) => row.index}
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
