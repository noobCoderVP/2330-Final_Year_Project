"use client"
import Image from "next/image";
import { useEffect, useState } from "react";
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import axios from "axios";

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

const attacks = ['Dos', 'Probe', 'R2L', 'U2R', 'normal'];

const COLUMNS: GridColDef[] = [{ 
  field: 'index', 
  headerName: 'Index', 
  width: 70, 
  valueGetter: (params) => params.row.index + 1
},
{ field: 'timestamp', headerName: 'Timestamp', width: 220 },
{ field: 'duration', headerName: 'Duration', width: 100 },
{ field: 'service', headerName: 'Service', width: 100 },
{ field: 'protocol_type', headerName: 'Protocol Type', width: 120 },
{ field: 'src_bytes', headerName: 'Source Bytes', width: 150 },
{ field: 'dst_bytes', headerName: 'Destination Bytes', width: 150 },
{ field: 'count', headerName: 'Count', width: 100 },
{ field: 'srv_count', headerName: 'Service Count', width: 120 },
{ field: 'attack', headerName: 'Attack', width: 100, valueGetter: (params) => attacks[params.row.attack] },
]

const rows = [
  { id: 1, lastName: 'Snow', firstName: 'Jon', age: 35 },
  { id: 2, lastName: 'Lannister', firstName: 'Cersei', age: 42 },
  { id: 3, lastName: 'Lannister', firstName: 'Jaime', age: 45 },
  { id: 4, lastName: 'Stark', firstName: 'Arya', age: 16 },
  { id: 5, lastName: 'Targaryen', firstName: 'Daenerys', age: null },
  { id: 6, lastName: 'Melisandre', firstName: null, age: 150 },
  { id: 7, lastName: 'Clifford', firstName: 'Ferrara', age: 44 },
  { id: 8, lastName: 'Frances', firstName: 'Rossini', age: 36 },
  { id: 9, lastName: 'Roxie', firstName: 'Harvey', age: 65 },
];


export default function Home() {
    const [logs, setLogs] = useState<log[]>([]);

    const fetchLogs = async () => {
      const result = await axios.get('http://localhost:8000/fetch');
      const data = result.data;
      // @ts-ignore
      setLogs(data.map((row, index: number) => ({ ...row, index })));
      console.log(result);
    }

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8765");

        socket.onopen = () => {
            console.log("WebSocket connected!");
        };

        socket.onmessage = (event) => {
            const message = event.data;
            console.log(message);
            setLogs((prevMessages) => [...prevMessages, message]);
        };

        fetchLogs();
        
        return () => {
          socket.close();
        };
      }, []);

    const onButtonClick = () => {
      const socket = new WebSocket("ws://localhost:8765");
      console.log(logs);
      socket.onopen = () => {
        socket.send("Hello world 2");
        console.log("Message sent");
      };
    }
    return (
        <main>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
            <h1 className="px-4 py-2 bg-black text-white m-2">Alert History</h1>
              <div style={{ height: '80vh'}}>
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
