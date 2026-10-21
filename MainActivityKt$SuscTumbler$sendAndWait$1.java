package ru.cyclone.susc_tumbler;

import kotlin.Metadata;
import kotlin.coroutines.Continuation;
import kotlin.coroutines.jvm.internal.ContinuationImpl;
import kotlin.coroutines.jvm.internal.DebugMetadata;

/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
@DebugMetadata(c = "ru.cyclone.susc_tumbler.MainActivityKt", f = "MainActivity.kt", i = {0, 0, 0}, l = {125}, m = "SuscTumbler$sendAndWait", n = {"manager", "timeoutMs", "timePassed"}, s = {"L$0", "J$0", "J$1"})
final class MainActivityKt$SuscTumbler$sendAndWait$1 extends ContinuationImpl {
    long J$0;
    long J$1;
    Object L$0;
    int label;
    /* synthetic */ Object result;

    MainActivityKt$SuscTumbler$sendAndWait$1(Continuation<? super MainActivityKt$SuscTumbler$sendAndWait$1> continuation) {
        super(continuation);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final Object invokeSuspend(Object obj) {
        this.result = obj;
        this.label |= Integer.MIN_VALUE;
        return MainActivityKt.SuscTumbler$sendAndWait(null, null, 0L, this);
    }
}
