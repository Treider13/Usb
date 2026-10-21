package ru.cyclone.susc_tumbler;

import java.util.Arrays;
import kotlin.Metadata;
import kotlin.collections.ArraysKt;
import kotlin.jvm.functions.Function1;
import kotlin.jvm.internal.Intrinsics;
import kotlin.jvm.internal.StringCompanionObject;

/* JADX INFO: compiled from: UsbSerialManager.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000\f\n\u0000\n\u0002\u0010\u000e\n\u0002\u0010\u0012\n\u0000\u001a\n\u0010\u0000\u001a\u00020\u0001*\u00020\u0002¨\u0006\u0003"}, d2 = {"toHexString", "", "", "app_release"}, k = 2, mv = {2, 0, 0}, xi = 48)
public final class UsbSerialManagerKt {
    public static final String toHexString(byte[] bArr) {
        Intrinsics.checkNotNullParameter(bArr, "<this>");
        return ArraysKt.joinToString$default(bArr, (CharSequence) " ", (CharSequence) null, (CharSequence) null, 0, (CharSequence) null, new Function1() { // from class: ru.cyclone.susc_tumbler.UsbSerialManagerKt$$ExternalSyntheticLambda0
            @Override // kotlin.jvm.functions.Function1
            public final Object invoke(Object obj) {
                return UsbSerialManagerKt.toHexString$lambda$0(((Byte) obj).byteValue());
            }
        }, 30, (Object) null);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final CharSequence toHexString$lambda$0(byte b) {
        StringCompanionObject stringCompanionObject = StringCompanionObject.INSTANCE;
        String str = String.format("%02X", Arrays.copyOf(new Object[]{Byte.valueOf(b)}, 1));
        Intrinsics.checkNotNullExpressionValue(str, "format(...)");
        return str;
    }
}
