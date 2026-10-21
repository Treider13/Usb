package ru.cyclone.susc_tumbler;

import androidx.compose.foundation.layout.ColumnScope;
import androidx.compose.foundation.layout.PaddingKt;
import androidx.compose.foundation.layout.RowScope;
import androidx.compose.material3.MaterialTheme;
import androidx.compose.material3.TextKt;
import androidx.compose.runtime.Composer;
import androidx.compose.runtime.ComposerKt;
import androidx.compose.runtime.internal.ComposableLambdaKt;
import androidx.compose.ui.Modifier;
import androidx.compose.ui.res.StringResources_androidKt;
import androidx.compose.ui.text.TextStyle;
import androidx.compose.ui.text.font.FontFamily;
import androidx.compose.ui.text.font.FontStyle;
import androidx.compose.ui.text.font.FontWeight;
import androidx.compose.ui.text.style.TextAlign;
import androidx.compose.ui.text.style.TextDecoration;
import androidx.compose.ui.unit.Dp;
import kotlin.Metadata;
import kotlin.Unit;
import kotlin.jvm.functions.Function1;
import kotlin.jvm.functions.Function2;
import kotlin.jvm.functions.Function3;
import kotlin.jvm.internal.Intrinsics;
import ru.cyclone.susc_tumbler.ui.theme.ThemeKt;

/* JADX INFO: compiled from: MainActivity.kt */
/* JADX INFO: loaded from: /tmp/decompiler/1fff03f604024d51870ca7c74eae34df/classes2.dex */
@Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
public final class ComposableSingletons$MainActivityKt {
    public static final ComposableSingletons$MainActivityKt INSTANCE = new ComposableSingletons$MainActivityKt();

    /* JADX INFO: renamed from: lambda-1, reason: not valid java name */
    public static Function2<Composer, Integer, Unit> f4lambda1 = ComposableLambdaKt.composableLambdaInstance(1414677098, false, new Function2<Composer, Integer, Unit>() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-1$1
        @Override // kotlin.jvm.functions.Function2
        public /* bridge */ /* synthetic */ Unit invoke(Composer composer, Integer num) {
            invoke(composer, num.intValue());
            return Unit.INSTANCE;
        }

        public final void invoke(Composer composer, int i) {
            ComposerKt.sourceInformation(composer, "C87@3653L13:MainActivity.kt#6o5wwo");
            if ((i & 3) == 2 && composer.getSkipping()) {
                composer.skipToGroupEnd();
                return;
            }
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(1414677098, i, -1, "ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt.lambda-1.<anonymous> (MainActivity.kt:87)");
            }
            MainActivityKt.SuscTumbler(composer, 0);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
            }
        }
    });

    /* JADX INFO: renamed from: lambda-2, reason: not valid java name */
    public static Function2<Composer, Integer, Unit> f5lambda2 = ComposableLambdaKt.composableLambdaInstance(-1543795408, false, new Function2<Composer, Integer, Unit>() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-2$1
        @Override // kotlin.jvm.functions.Function2
        public /* bridge */ /* synthetic */ Unit invoke(Composer composer, Integer num) {
            invoke(composer, num.intValue());
            return Unit.INSTANCE;
        }

        public final void invoke(Composer composer, int i) {
            ComposerKt.sourceInformation(composer, "C86@3617L63:MainActivity.kt#6o5wwo");
            if ((i & 3) != 2 || !composer.getSkipping()) {
                if (ComposerKt.isTraceInProgress()) {
                    ComposerKt.traceEventStart(-1543795408, i, -1, "ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt.lambda-2.<anonymous> (MainActivity.kt:86)");
                }
                ThemeKt.Susc_tumblerTheme(false, false, ComposableSingletons$MainActivityKt.INSTANCE.m1786getLambda1$app_release(), composer, 384, 3);
                if (ComposerKt.isTraceInProgress()) {
                    ComposerKt.traceEventEnd();
                    return;
                }
                return;
            }
            composer.skipToGroupEnd();
        }
    });

    /* JADX INFO: renamed from: lambda-3, reason: not valid java name */
    public static Function3<RowScope, Composer, Integer, Unit> f6lambda3 = ComposableLambdaKt.composableLambdaInstance(-1569922968, false, new Function3<RowScope, Composer, Integer, Unit>() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-3$1
        @Override // kotlin.jvm.functions.Function3
        public /* bridge */ /* synthetic */ Unit invoke(RowScope rowScope, Composer composer, Integer num) {
            invoke(rowScope, composer, num.intValue());
            return Unit.INSTANCE;
        }

        public final void invoke(RowScope Button, Composer composer, int i) {
            Intrinsics.checkNotNullParameter(Button, "$this$Button");
            ComposerKt.sourceInformation(composer, "C490@20333L29,490@20328L35:MainActivity.kt#6o5wwo");
            if ((i & 17) == 16 && composer.getSkipping()) {
                composer.skipToGroupEnd();
                return;
            }
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventStart(-1569922968, i, -1, "ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt.lambda-3.<anonymous> (MainActivity.kt:490)");
            }
            TextKt.Text--4IGK_g(StringResources_androidKt.stringResource(R.string.save, composer, 0), (Modifier) null, 0L, 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, (TextStyle) null, composer, 0, 0, 131070);
            if (ComposerKt.isTraceInProgress()) {
                ComposerKt.traceEventEnd();
            }
        }
    });

    /* JADX INFO: renamed from: lambda-4, reason: not valid java name */
    public static Function3<ColumnScope, Composer, Integer, Unit> f7lambda4 = ComposableLambdaKt.composableLambdaInstance(-1609822531, false, new Function3<ColumnScope, Composer, Integer, Unit>() { // from class: ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt$lambda-4$1
        @Override // kotlin.jvm.functions.Function3
        public /* bridge */ /* synthetic */ Unit invoke(ColumnScope columnScope, Composer composer, Integer num) {
            invoke(columnScope, composer, num.intValue());
            return Unit.INSTANCE;
        }

        public final void invoke(ColumnScope Card, Composer composer, int i) {
            Intrinsics.checkNotNullParameter(Card, "$this$Card");
            ComposerKt.sourceInformation(composer, "C497@20715L11,494@20539L226:MainActivity.kt#6o5wwo");
            if ((i & 17) != 16 || !composer.getSkipping()) {
                if (ComposerKt.isTraceInProgress()) {
                    ComposerKt.traceEventStart(-1609822531, i, -1, "ru.cyclone.susc_tumbler.ComposableSingletons$MainActivityKt.lambda-4.<anonymous> (MainActivity.kt:494)");
                }
                TextKt.Text--4IGK_g("Подключите питание устройства", PaddingKt.padding-3ABfNKs(Modifier.Companion, Dp.constructor-impl(16)), MaterialTheme.INSTANCE.getColorScheme(composer, MaterialTheme.$stable).getOnErrorContainer-0d7_KjU(), 0L, (FontStyle) null, (FontWeight) null, (FontFamily) null, 0L, (TextDecoration) null, (TextAlign) null, 0L, 0, false, 0, 0, (Function1) null, (TextStyle) null, composer, 54, 0, 131064);
                if (ComposerKt.isTraceInProgress()) {
                    ComposerKt.traceEventEnd();
                    return;
                }
                return;
            }
            composer.skipToGroupEnd();
        }
    });

    /* JADX INFO: renamed from: lambda-5, reason: not valid java name */
    public static Function2<Composer, Integer, Unit> f8lambda5 = ComposableLambdaKt.composableLambdaInstance(-325203374, false, ComposableSingletons$MainActivityKt$lambda5$1.INSTANCE);

    /* JADX INFO: renamed from: getLambda-1$app_release, reason: not valid java name */
    public final Function2<Composer, Integer, Unit> m1786getLambda1$app_release() {
        return f4lambda1;
    }

    /* JADX INFO: renamed from: getLambda-2$app_release, reason: not valid java name */
    public final Function2<Composer, Integer, Unit> m1787getLambda2$app_release() {
        return f5lambda2;
    }

    /* JADX INFO: renamed from: getLambda-3$app_release, reason: not valid java name */
    public final Function3<RowScope, Composer, Integer, Unit> m1788getLambda3$app_release() {
        return f6lambda3;
    }

    /* JADX INFO: renamed from: getLambda-4$app_release, reason: not valid java name */
    public final Function3<ColumnScope, Composer, Integer, Unit> m1789getLambda4$app_release() {
        return f7lambda4;
    }

    /* JADX INFO: renamed from: getLambda-5$app_release, reason: not valid java name */
    public final Function2<Composer, Integer, Unit> m1790getLambda5$app_release() {
        return f8lambda5;
    }
}
