import argparseimport socketimport timeimport threadingimport sysdef main():    parser = argparse.ArgumentParser(description="simpleperf")    mode = parser.add_mutually_exclusive_group(required=True)    mode.add_argument("-s", "--server", action="store_true", help="enable server mode")    mode.add_argument("-c", "--client", action="store_true", help="enable client mode")    parser.add_argument("-b", "--bind", type=str, default="0.0.0.0", help="IP address of the server's interface to bind")    parser.add_argument("-I", "--serverip", type=str, help="IP address of the simpleperf server")    parser.add_argument("-p", "--port", type=int, default=8088, help="port number for the server to listen on")    parser.add_argument("-t", "--time", type=int, default=25, help="duration in seconds for which data should be generated and sent to the server")    parser.add_argument("-f", "--format", type=str, default="MB", choices=["B", "KB", "MB"], help="format of the summary of results")    parser.add_argument("-i", "--interval", type=int, help="print statistics per interval second")    parser.add_argument("-P", "--parallel", type=int, default=1, help="number of parallel connections")    parser.add_argument("-n", "--num", type=str, help="number of bytes to transfer")    args = parser.parse_args()    if args.server:        run_server(args.bind, args.port, args.format)    elif args.client:        if not args.serverip:            print("Error: Server IP address is required in client mode.")            return        if args.num:            bytes_to_transfer = parse_num_bytes(args.num)            if bytes_to_transfer is None:                print("Error: Invalid value for -n/--num.")                return            args.time = None        else:            bytes_to_transfer = None        run_client(args.serverip, args.port, args.time, args.format, args.interval, args.parallel, bytes_to_transfer)def parse_num_bytes(num_str):    try:        if num_str[-1] == "B":            return int(num_str[:-1])        elif num_str[-2:] == "KB":            return int(num_str[:-2]) * 1000        elif num_str[-2:] == "MB":            return int(num_str[:-2]) * 1000000    except ValueError:        pass    return Nonedef run_server(bind_ip, port, data_format):    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        server_socket.bind((bind_ip, port))        server_socket.listen()        print("---------------------------------------------")        print(f"A simpleperf server is listening on port {port}")        print("---------------------------------------------")        while True:            conn, addr = server_socket.accept()            threading.Thread(target=handle_client, args=(conn, addr, data_format)).start()def handle_client(conn, addr, data_format):    with conn:        print(f"A simpleperf client with {addr[0]}:{addr[1]} is connected")        total_received = 0        start_time = time.time()        while True:            data = conn.recv(1000)            if not data:                break            total_received += len(data)        elapsed_time = time.time() - start_time        transfer_size = convert_bytes(total_received, data_format)        bandwidth = (total_received * 8) / (elapsed_time * 1000000)        print("ID Interval Transfer Bandwidth")        print(f"{addr[0]}:{addr[1]} 0.0 - {elapsed_time:.1f} {transfer_size} {bandwidth:.2f} Mbps")        conn.sendall(b"acknowledgement")        print(f"A simpleperf client with {addr[0]}:{addr[1]} has finished")        response = conn.recv(1000)        if response == b"BYE":            conn.sendall(b"ACK")            print(f"A simpleperf client with {addr[0]}:{addr[1]} has finished")def run_client(server_ip, server_port, time_duration, data_format, interval, parallel, bytes_to_transfer):    if parallel > 1:        threads = []        for i in range(parallel):            t = threading.Thread(target=run_single_client, args=(                server_ip, server_port, time_duration, data_format, interval, bytes_to_transfer))            threads.append(t)            t.start()        for t in threads:            t.join()    else:        run_single_client(server_ip, server_port, time_duration, data_format, interval, bytes_to_transfer)def run_single_client(server_ip, server_port, time_duration, data_format, interval, bytes_to_transfer):    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:        client_socket.connect((server_ip, server_port))        print(f"Client connected with {server_ip}:{server_port}")        start_time = time.time()        total_sent = 0        next_interval = start_time + interval if interval else None        while (time_duration and time.time() - start_time < time_duration) or (                bytes_to_transfer and total_sent < bytes_to_transfer):            data = b'\x00' * 1000            client_socket.sendall(data)            total_sent += len(data)            if interval and time.time() >= next_interval:                elapsed_time = time.time() - start_time                transfer_size = convert_bytes(total_sent, data_format)                bandwidth = (total_sent * 8) / (elapsed_time * 1000000)                print(                    f"{server_ip}:{server_port} {elapsed_time:.1f} - {next_interval:.1f} {transfer_size} {bandwidth:.2f} Mbps")                next_interval += interval        client_socket.sendall(b"BYE")        response = client_socket.recv(1024)        if response == b"ACK":            client_socket.close()            elapsed_time = time.time() - start_time            transfer_size = convert_bytes(total_sent, data_format)            bandwidth = (total_sent * 8) / (elapsed_time * 1000000)            print("ID Interval Transfer Bandwidth")            print(f"{server_ip}:{server_port} 0.0 - {elapsed_time:.1f} {transfer_size} {bandwidth:.2f} Mbps")def convert_bytes(num_bytes, data_format):        if data_format == "B":            return f"{num_bytes} B"        elif data_format == "KB":            return f"{num_bytes / 1000:.2f} KB"        elif data_format == "MB":            return f"{num_bytes / 1000000:.2f} MB"if __name__ == "__main__":        main()