package ru.cyclone.susc_tumbler;

import androidx.compose.runtime.MutableState;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import kotlin.Metadata;
import kotlin.Unit;
import kotlin.coroutines.Continuation;
import kotlin.coroutines.jvm.internal.DebugMetadata;
import kotlin.coroutines.jvm.internal.SuspendLambda;
import kotlin.jvm.functions.Function2;
import kotlinx.coroutines.CoroutineScope;

/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lkotlinx/coroutines/CoroutineScope;"}, k = 3, mv = {2, 0, 0}, xi = 48)
@DebugMetadata(c = "ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$2$1", f = "MainActivity.kt", i = {0, 2}, l = {153, 157, 165}, m = "invokeSuspend", n = {"previousPowerOn", "previousPowerOn"}, s = {"I$0", "I$0"})
final class MainActivityKt$SuscTumbler$2$1 extends SuspendLambda implements Function2<CoroutineScope, Continuation<? super Unit>, Object> {
    final /* synthetic */ MutableState<UsbSerialPort> $connectedPort$delegate;
    final /* synthetic */ MutableState<Boolean> $isDevicePowerOn$delegate;
    final /* synthetic */ UsbSerialManager $usbSerialManager;
    int I$0;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    MainActivityKt$SuscTumbler$2$1(UsbSerialManager usbSerialManager, MutableState<UsbSerialPort> mutableState, MutableState<Boolean> mutableState2, Continuation<? super MainActivityKt$SuscTumbler$2$1> continuation) {
        super(2, continuation);
        this.$usbSerialManager = usbSerialManager;
        this.$connectedPort$delegate = mutableState;
        this.$isDevicePowerOn$delegate = mutableState2;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final Continuation<Unit> create(Object obj, Continuation<?> continuation) {
        return new MainActivityKt$SuscTumbler$2$1(this.$usbSerialManager, this.$connectedPort$delegate, this.$isDevicePowerOn$delegate, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final Object invoke(CoroutineScope coroutineScope, Continuation<? super Unit> continuation) {
        return ((MainActivityKt$SuscTumbler$2$1) create(coroutineScope, continuation)).invokeSuspend(Unit.INSTANCE);
    }

    /* JADX WARN: Code restructure failed: missing block: B:26:0x008b, code lost:
    
        if (ru.cyclone.susc_tumbler.MainActivityKt.SuscTumbler$performInitialization(r18.$usbSerialManager, r18) == r1) goto L32;
     */
    /* JADX WARN: Multi-variable type inference failed */
    /* JADX WARN: Removed duplicated region for block: B:22:0x006f  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0095  */
    /* JADX WARN: Type inference failed for: r2v10 */
    /* JADX WARN: Type inference failed for: r2v14, types: [int] */
    /* JADX WARN: Type inference failed for: r2v18 */
    /* JADX WARN: Type inference failed for: r2v19 */
    /* JADX WARN: Type inference failed for: r2v20 */
    /* JADX WARN: Type inference failed for: r2v21 */
    /* JADX WARN: Type inference failed for: r2v22 */
    /* JADX WARN: Type inference failed for: r2v3 */
    /* JADX WARN: Type inference failed for: r2v4, types: [int] */
    /* JADX WARN: Type inference failed for: r2v7 */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:31:0x00ad -> B:17:0x0046). Please report as a decompilation issue!!! */
    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct code enable 'Show inconsistent code' option in preferences
    */
    public final java.lang.Object invokeSuspend(java.lang.Object r19) {
        /*
            r18 = this;
            r0 = r18
            java.lang.Object r1 = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED()
            int r2 = r0.label
            r3 = 3000(0xbb8, double:1.482E-320)
            r5 = 3
            r6 = 2
            r7 = 1
            java.lang.String r8 = "SUSC_TUMBLER"
            r9 = 0
            if (r2 == 0) goto L32
            if (r2 == r7) goto L2a
            if (r2 == r6) goto L26
            if (r2 != r5) goto L1e
            int r2 = r0.I$0
            kotlin.ResultKt.throwOnFailure(r19)
            goto L46
        L1e:
            java.lang.IllegalStateException r1 = new java.lang.IllegalStateException
            java.lang.String r2 = "call to 'resume' before 'invoke' with coroutine"
            r1.<init>(r2)
            throw r1
        L26:
            kotlin.ResultKt.throwOnFailure(r19)
            goto L8e
        L2a:
            int r2 = r0.I$0
            kotlin.ResultKt.throwOnFailure(r19)
            r10 = r19
            goto L6b
        L32:
            kotlin.ResultKt.throwOnFailure(r19)
            androidx.compose.runtime.MutableState<com.hoho.android.usbserial.driver.UsbSerialPort> r2 = r0.$connectedPort$delegate
            com.hoho.android.usbserial.driver.UsbSerialPort r2 = ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$lambda$4(r2)
            if (r2 != 0) goto L45
            androidx.compose.runtime.MutableState<java.lang.Boolean> r1 = r0.$isDevicePowerOn$delegate
            ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$lambda$11(r1, r9)
            kotlin.Unit r1 = kotlin.Unit.INSTANCE
            return r1
        L45:
            r2 = r9
        L46:
            ru.cyclone.susc_tumbler.DebugLogger r10 = ru.cyclone.susc_tumbler.DebugLogger.INSTANCE
            java.lang.String r11 = "Requesting status (RANGE)..."
            r10.i(r8, r11)
            ru.cyclone.susc_tumbler.CommandBuilder r12 = ru.cyclone.susc_tumbler.CommandBuilder.INSTANCE
            r16 = 4
            r17 = 0
            java.lang.String r13 = "RANGE"
            r14 = 0
            r15 = 0
            byte[] r10 = ru.cyclone.susc_tumbler.CommandBuilder.buildCommand$default(r12, r13, r14, r15, r16, r17)
            ru.cyclone.susc_tumbler.UsbSerialManager r11 = r0.$usbSerialManager
            r12 = r0
            kotlin.coroutines.Continuation r12 = (kotlin.coroutines.Continuation) r12
            r0.I$0 = r2
            r0.label = r7
            java.lang.Object r10 = ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$sendAndWait(r11, r10, r3, r12)
            if (r10 != r1) goto L6b
            goto Laf
        L6b:
            byte[] r10 = (byte[]) r10
            if (r10 == 0) goto L95
            androidx.compose.runtime.MutableState<java.lang.Boolean> r10 = r0.$isDevicePowerOn$delegate
            boolean r10 = ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$lambda$10(r10)
            if (r10 == 0) goto L8e
            if (r2 != 0) goto L8e
            ru.cyclone.susc_tumbler.DebugLogger r2 = ru.cyclone.susc_tumbler.DebugLogger.INSTANCE
            java.lang.String r10 = "Device powered on - starting initialization"
            r2.i(r8, r10)
            ru.cyclone.susc_tumbler.UsbSerialManager r2 = r0.$usbSerialManager
            r10 = r0
            kotlin.coroutines.Continuation r10 = (kotlin.coroutines.Continuation) r10
            r0.label = r6
            java.lang.Object r2 = ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$performInitialization(r2, r10)
            if (r2 != r1) goto L8e
            goto Laf
        L8e:
            androidx.compose.runtime.MutableState<java.lang.Boolean> r2 = r0.$isDevicePowerOn$delegate
            boolean r2 = ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$lambda$10(r2)
            goto La2
        L95:
            ru.cyclone.susc_tumbler.DebugLogger r2 = ru.cyclone.susc_tumbler.DebugLogger.INSTANCE
            java.lang.String r10 = "Timeout. Assuming power is off."
            r2.i(r8, r10)
            androidx.compose.runtime.MutableState<java.lang.Boolean> r2 = r0.$isDevicePowerOn$delegate
            ru.cyclone.susc_tumbler.MainActivityKt.access$SuscTumbler$lambda$11(r2, r9)
            r2 = r9
        La2:
            r10 = r0
            kotlin.coroutines.Continuation r10 = (kotlin.coroutines.Continuation) r10
            r0.I$0 = r2
            r0.label = r5
            java.lang.Object r10 = kotlinx.coroutines.DelayKt.delay(r3, r10)
            if (r10 != r1) goto L46
        Laf:
            return r1
        */
        throw new UnsupportedOperationException("Method not decompiled: ru.cyclone.susc_tumbler.MainActivityKt$SuscTumbler$2$1.invokeSuspend(java.lang.Object):java.lang.Object");
    }
}
