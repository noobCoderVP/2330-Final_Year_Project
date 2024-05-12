"use client";
import {
    Table,
    TableHeader,
    TableColumn,
    TableBody,
    TableRow,
    TableCell,
    Pagination,
    getKeyValue,
} from "@nextui-org/react";
import { useEffect, useState, useMemo } from "react";

interface Log{
    timestamp: string;
    switchid: number;
    source: string;
    destination: string;
    in_port: number;
}

export default function Home() {
    const [messages, setMessages] = useState<Log[]>([]);

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8765");

        socket.onopen = () => {
            console.log("WebSocket connected!");
        };

        socket.onmessage = (event) => {
            const message = event.data;
            console.log(message);
            setMessages((prevMessages) => [
                ...prevMessages,
                JSON.parse(message),
            ]);
        };

        return () => {
            socket.close();
        };
    }, []);

    const [page, setPage] = useState(1);
    const rowsPerPage = 4;

    const pages = Math.ceil(messages.length / rowsPerPage);

    const items = useMemo(() => {
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;

        return messages.slice(start, end);
    }, [page, messages]);

    return (
        <main>
            <div>
                <h1 className="px-4 py-2 bg-black text-white">
                    Controller logs
                </h1>
                <Table
                    aria-label="Logs of controller"
                    bottomContent={
                        <div className="flex w-full justify-center">
                            <Pagination
                                isCompact
                                showControls
                                showShadow
                                color="secondary"
                                page={page}
                                total={pages}
                                onChange={(page) => setPage(page)}
                            />
                        </div>
                    }
                    classNames={{
                        wrapper: "min-h-[222px]",
                    }}
                >
                    <TableHeader>
                        <TableColumn key="timestamp">Timestamp</TableColumn>
                        <TableColumn key="switchid">Switch ID</TableColumn>
                        <TableColumn key="source">Source</TableColumn>
                        <TableColumn key="destination">Destination</TableColumn>
                        <TableColumn key="in_port">Input port</TableColumn>
                    </TableHeader>
                    <TableBody items={items}>
                        {(item) => (
                            <TableRow key={item.timestamp}>
                                {(columnKey) => (
                                    <TableCell>
                                        {getKeyValue(item, columnKey)}
                                    </TableCell>
                                )}
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </main>
    );
}
