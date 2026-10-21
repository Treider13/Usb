package ru.cyclone.susc_tumbler;

import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import kotlin.Metadata;
import kotlin.Pair;
import kotlin.TuplesKt;
import kotlin.UByte;
import kotlin.collections.ArraysKt;
import kotlin.collections.CollectionsKt;
import kotlin.collections.IntIterator;
import kotlin.collections.MapsKt;
import kotlin.jvm.internal.Intrinsics;
import kotlin.ranges.IntRange;
import kotlin.ranges.RangesKt;

/* JADX INFO: compiled from: CommandBuilder.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000:\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0002\b\u0003\n\u0002\u0010\b\n\u0002\b\u0003\n\u0002\u0010\u0005\n\u0000\n\u0002\u0010$\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u0012\n\u0002\b\u0004\n\u0002\u0010\u000b\n\u0000\n\u0002\u0018\u0002\n\u0000\bÇ\u0002\u0018\u00002\u00020\u0001B\t\b\u0002¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0013\u001a\u00020\t2\u0006\u0010\u0014\u001a\u00020\u0015H\u0002J$\u0010\u0016\u001a\u0004\u0018\u00010\u00152\u0006\u0010\u0017\u001a\u00020\f2\b\b\u0002\u0010\u0018\u001a\u00020\u00052\b\b\u0002\u0010\u0019\u001a\u00020\u001aJ\u001c\u0010\u001b\u001a\u0010\u0012\u0004\u0012\u00020\f\u0012\u0004\u0012\u00020\u0005\u0018\u00010\u001c2\u0006\u0010\u0014\u001a\u00020\u0015R\u000e\u0010\u0004\u001a\u00020\u0005X\u0082T¢\u0006\u0002\n\u0000R\u000e\u0010\u0006\u001a\u00020\u0005X\u0082T¢\u0006\u0002\n\u0000R\u000e\u0010\u0007\u001a\u00020\u0005X\u0082T¢\u0006\u0002\n\u0000R\u000e\u0010\b\u001a\u00020\tX\u0082T¢\u0006\u0002\n\u0000R\u001a\u0010\n\u001a\u000e\u0012\u0004\u0012\u00020\f\u0012\u0004\u0012\u00020\t0\u000bX\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010\r\u001a\u000e\u0012\u0004\u0012\u00020\u0005\u0012\u0004\u0012\u00020\t0\u000bX\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010\u000e\u001a\u000e\u0012\u0004\u0012\u00020\t\u0012\u0004\u0012\u00020\u00050\u000bX\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010\u000f\u001a\u000e\u0012\u0004\u0012\u00020\u0005\u0012\u0004\u0012\u00020\t0\u000bX\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010\u0010\u001a\u000e\u0012\u0004\u0012\u00020\t\u0012\u0004\u0012\u00020\u00050\u000bX\u0082\u0004¢\u0006\u0002\n\u0000R\u000e\u0010\u0011\u001a\u00020\u0005X\u0082\u000e¢\u0006\u0002\n\u0000R\u000e\u0010\u0012\u001a\u00020\fX\u0082\u000e¢\u0006\u0002\n\u0000¨\u0006\u001d"}, d2 = {"Lru/cyclone/susc_tumbler/CommandBuilder;", "", "<init>", "()V", "CRC_POLY", "", "CRC_INIT", "CRC_XOR_OUT", "READ_FLAG", "", "registryAddresses", "", "", "valuesBW0", "sliderBW0", "valuesBW1", "sliderBW1", "boundWithNumber", "registryAddress", "calculateCrc", "data", "", "buildCommand", "regName", "value", "write", "", "parseResponse", "Lkotlin/Pair;", "app_release"}, k = 1, mv = {2, 0, 0}, xi = 48)
public final class CommandBuilder {
    public static final int $stable;
    private static final int CRC_INIT = 255;
    private static final int CRC_POLY = 49;
    private static final int CRC_XOR_OUT = 0;
    private static final byte READ_FLAG = -128;
    private static int boundWithNumber;
    private static String registryAddress;
    private static final Map<Byte, Integer> sliderBW0;
    private static final Map<Byte, Integer> sliderBW1;
    private static final Map<Integer, Byte> valuesBW0;
    private static final Map<Integer, Byte> valuesBW1;
    public static final CommandBuilder INSTANCE = new CommandBuilder();
    private static final Map<String, Byte> registryAddresses = MapsKt.mapOf(TuplesKt.to("USER_LED", (byte) 0), TuplesKt.to("SS_RATE", (byte) 6), TuplesKt.to("RANGE", (byte) 7), TuplesKt.to("USER_CODE_ID", (byte) 64), TuplesKt.to("START_CFG", (byte) 65), TuplesKt.to("CFG_DONE", (byte) 66), TuplesKt.to("WR_DONE", (byte) 70), TuplesKt.to("SET_EE_CFG", (byte) 71), TuplesKt.to("ENABLE_SOSC12", (byte) 72));

    private CommandBuilder() {
    }

    static {
        char c = 3;
        Map<Integer, Byte> mapMapOf = MapsKt.mapOf(TuplesKt.to(3, (byte) 3), TuplesKt.to(4, (byte) 4), TuplesKt.to(5, (byte) 14), TuplesKt.to(6, (byte) 13), TuplesKt.to(7, (byte) 12), TuplesKt.to(8, (byte) 11), TuplesKt.to(9, (byte) 10), TuplesKt.to(10, (byte) 9), TuplesKt.to(11, (byte) 8));
        valuesBW0 = mapMapOf;
        Set<Map.Entry<Integer, Byte>> setEntrySet = mapMapOf.entrySet();
        LinkedHashMap linkedHashMap = new LinkedHashMap(RangesKt.coerceAtLeast(MapsKt.mapCapacity(CollectionsKt.collectionSizeOrDefault(setEntrySet, 10)), 16));
        Iterator<T> it = setEntrySet.iterator();
        while (it.hasNext()) {
            Map.Entry entry = (Map.Entry) it.next();
            Pair pair = TuplesKt.to(Byte.valueOf(((Number) entry.getValue()).byteValue()), Integer.valueOf(((Number) entry.getKey()).intValue()));
            linkedHashMap.put(pair.getFirst(), pair.getSecond());
            c = c;
        }
        sliderBW0 = linkedHashMap;
        Pair[] pairArr = new Pair[6];
        pairArr[0] = TuplesKt.to(5, (byte) 15);
        pairArr[1] = TuplesKt.to(6, (byte) 20);
        pairArr[2] = TuplesKt.to(7, (byte) 19);
        pairArr[c] = TuplesKt.to(8, (byte) 18);
        pairArr[4] = TuplesKt.to(9, (byte) 17);
        pairArr[5] = TuplesKt.to(10, (byte) 16);
        Map<Integer, Byte> mapMapOf2 = MapsKt.mapOf(pairArr);
        valuesBW1 = mapMapOf2;
        Set<Map.Entry<Integer, Byte>> setEntrySet2 = mapMapOf2.entrySet();
        LinkedHashMap linkedHashMap2 = new LinkedHashMap(RangesKt.coerceAtLeast(MapsKt.mapCapacity(CollectionsKt.collectionSizeOrDefault(setEntrySet2, 10)), 16));
        Iterator<T> it2 = setEntrySet2.iterator();
        while (it2.hasNext()) {
            Map.Entry entry2 = (Map.Entry) it2.next();
            Pair pair2 = TuplesKt.to(Byte.valueOf(((Number) entry2.getValue()).byteValue()), Integer.valueOf(((Number) entry2.getKey()).intValue()));
            linkedHashMap2.put(pair2.getFirst(), pair2.getSecond());
        }
        sliderBW1 = linkedHashMap2;
        registryAddress = "RANGE";
        $stable = 8;
    }

    private final byte calculateCrc(byte[] data) {
        int i = 255;
        for (byte b : data) {
            i ^= b & UByte.MAX_VALUE;
            Iterator<Integer> it = new IntRange(0, 7).iterator();
            while (it.hasNext()) {
                ((IntIterator) it).nextInt();
                int i2 = i & 128;
                int i3 = i << 1;
                if (i2 != 0) {
                    i3 ^= CRC_POLY;
                }
                i = i3 & 255;
            }
        }
        return (byte) i;
    }

    public static /* synthetic */ byte[] buildCommand$default(CommandBuilder commandBuilder, String str, int i, boolean z, int i2, Object obj) {
        if ((i2 & 2) != 0) {
            i = 0;
        }
        if ((i2 & 4) != 0) {
            z = false;
        }
        return commandBuilder.buildCommand(str, i, z);
    }

    /* JADX WARN: Failed to restore switch over string. Please report as a decompilation issue */
    public final byte[] buildCommand(String regName, int value, boolean write) {
        byte bByteValue;
        Intrinsics.checkNotNullParameter(regName, "regName");
        byte bByteValue2 = write ? registryAddresses.getOrDefault(regName, (byte) 0).byteValue() : (byte) (registryAddresses.getOrDefault(regName, (byte) 0).byteValue() | (-128));
        registryAddress = regName;
        if (write) {
            switch (regName.hashCode()) {
                case -1180143777:
                    if (!regName.equals("SS_RATE")) {
                        bByteValue = 0;
                    } else if (boundWithNumber == 0) {
                        Byte b = valuesBW0.get(Integer.valueOf(value));
                        if (b == null) {
                            return null;
                        }
                        bByteValue = b.byteValue();
                    } else {
                        Byte b2 = valuesBW1.get(Integer.valueOf(value));
                        if (b2 == null) {
                            return null;
                        }
                        bByteValue = b2.byteValue();
                    }
                    break;
                case 77742365:
                    if (!regName.equals("RANGE")) {
                        bByteValue = 0;
                    } else {
                        boundWithNumber = value;
                        bByteValue = value != 0 ? (byte) 9 : (byte) 36;
                    }
                    break;
                case 517430135:
                    bByteValue = !regName.equals("USER_LED") ? (byte) 0 : (byte) value;
                    break;
                case 658575047:
                    bByteValue = !regName.equals("START_CFG") ? (byte) 0 : (byte) 1;
                    break;
                default:
                    bByteValue = 0;
                    break;
            }
        } else {
            bByteValue = 0;
        }
        byte[] bArr = {bByteValue2, 0, bByteValue};
        return new byte[]{bArr[0], bArr[1], bArr[2], calculateCrc(bArr)};
    }

    public final Pair<String, Integer> parseResponse(byte[] data) {
        int iIntValue;
        Intrinsics.checkNotNullParameter(data, "data");
        if (data.length < 4) {
            return null;
        }
        int i = 0;
        i = 0;
        i = 0;
        i = 0;
        if (calculateCrc(ArraysKt.sliceArray(data, new IntRange(0, 2))) != data[3]) {
            return null;
        }
        String str = registryAddress;
        int iHashCode = str.hashCode();
        if (iHashCode != -1180143777) {
            if (iHashCode != 77742365) {
                if (iHashCode == 517430135 && str.equals("USER_LED")) {
                    i = data[2];
                }
            } else if (str.equals("RANGE")) {
                i = data[2] == '\t' ? 1 : 0;
                boundWithNumber = i;
            }
        } else if (str.equals("SS_RATE")) {
            if (boundWithNumber == 0) {
                iIntValue = sliderBW0.getOrDefault(Byte.valueOf(data[2]), 3).intValue();
            } else {
                iIntValue = sliderBW1.getOrDefault(Byte.valueOf(data[2]), 5).intValue();
            }
            i = iIntValue;
        }
        return new Pair<>(str, Integer.valueOf(i));
    }
}
