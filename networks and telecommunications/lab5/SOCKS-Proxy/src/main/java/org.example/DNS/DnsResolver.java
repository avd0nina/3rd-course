package org.example.DNS;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.xbill.DNS.*;
import org.xbill.DNS.Record;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.nio.channels.SelectionKey;
import java.nio.charset.StandardCharsets;
import java.util.AbstractMap;
import java.util.HashMap;
import java.util.Map;

@Slf4j
public class DnsResolver {
    public static final int DNS_PORT = 53;
    private final DatagramChannel dnsChannel;
    private int senderID;

    @Getter
    private final HashMap<Integer, Map.Entry<Integer, SelectionKey>> clientMatch;

    public DnsResolver(DatagramChannel dnsChannel) {
        this.dnsChannel = dnsChannel;
        this.senderID = 0;
        this.clientMatch = new HashMap<>();
    }

    public void resolve(byte[] addr, int port, SelectionKey key) {
        try {
            Message message = new Message();
            Record record = Record.newRecord(Name.fromString(
                    new String(addr, StandardCharsets.UTF_8) + '.'), Type.A, DClass.IN);
            message.addRecord(record, Section.QUESTION);
            Header header = message.getHeader();
            header.setFlag(Flags.AD);
            header.setFlag(Flags.RD);
            header.setID(senderID);
            clientMatch.put(senderID, new AbstractMap.SimpleEntry<>(port, key));
            senderID++;
            dnsChannel.write(ByteBuffer.wrap(message.toWire()));
        } catch (TextParseException exc) {
            throw new IllegalArgumentException("DNS resolve exc: ", exc);
        } catch (IOException exc) {
            throw new IllegalArgumentException("dns channel write fail: ", exc);
        }
    }
}
