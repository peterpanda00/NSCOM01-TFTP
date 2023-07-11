import socket
import os

# Function to prompt for server IP address
def prompt_server_ip():
    server_ip = input("Enter the server IP address: ")
    return server_ip

# Function to upload a file to the TFTP server
def upload_file(server_ip):
    # Prompt for the file path
    file_path = input("Enter the file path to upload: ")

    try:
        # Verify file accessibility and privileges
        with open(file_path, 'rb') as file:
            # Establish connection with TFTP server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.settimeout(5)  # Set timeout for unresponsive server

            # Start TFTP protocol for uploading
            # Send the write request packet
            request_packet = bytearray([0x00, 0x02])  # Opcode for write request
            request_packet.extend(file_path.encode())
            request_packet.extend(b'\x00')  # Mode, e.g., "octet"
            client_socket.sendto(request_packet, (server_ip, 69))

            # Receive the acknowledgment packet
            ack_packet, server_address = client_socket.recvfrom(1024)
            opcode = ack_packet[1]
            if opcode == 5:
                error_code = ack_packet[3:5]
                error_message = ack_packet[5:].decode()
                raise Exception(f"Error {error_code}: {error_message}")

            # Get the file size
            file_size = os.path.getsize(file_path)

            # Send the data packets
            block_number = 1
            while True:
                data = file.read(512)
                if not data:
                    break

                data_packet = bytearray([0x00, 0x03])  # Opcode for data packet
                data_packet.extend(block_number.to_bytes(2, 'big'))  # Block number
                data_packet.extend(data)  # Data
                client_socket.sendto(data_packet, server_address)

                # Receive the acknowledgment packet
                while True:
                    try:
                        ack_packet, server_address = client_socket.recvfrom(1024)
                        if ack_packet[1] == 4 and int.from_bytes(ack_packet[2:4], 'big') == block_number:
                            break
                    except socket.timeout:
                        print("Timeout. Resending the data packet.")
                        client_socket.sendto(data_packet, server_address)

                block_number += 1

                # Print progress
                progress = file.tell() / file_size * 100
                print(f"Upload progress: {progress:.2f}%")

            print("File upload successful!")

    except FileNotFoundError:
        print("File not found.")
    except PermissionError:
        print("Access violation. Check file permissions.")
    except socket.timeout:
        print("Server is unresponsive.")
    except Exception as e:
        print("Error occurred:", str(e))
    finally:
        client_socket.close()
        
# Main program flow
if __name__ == '__main__':
    # Prompt for server IP address
    server_ip = prompt_server_ip()

    # Perform file upload
    upload_file(server_ip)
